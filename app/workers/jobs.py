"""
Background jobs pour traitement asynchrone des emails.

Ces jobs sont exécutés par les workers RQ (Redis Queue) et gèrent
les workflows métier de Léonie :
- NOUVEAU_DOSSIER : Création client + dossier Drive
- ENVOI_DOCUMENTS : Traitement documents + upload Drive
- MODIFIER_LISTE : Modification liste pièces attendues
"""

import base64
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import structlog

# Services
from app.services.drive import DriveManager
from app.services.mistral import MistralService

# Utils DB
from app.utils.db import (
    get_courtier_by_id,
)
from uuid import UUID

logger = structlog.get_logger()


def process_nouveau_dossier(
    courtier_id: str,
    email_data: dict,
    classification: dict
) -> dict:
    """
    Crée un nouveau dossier client (Job RQ).

    Étapes :
    1. Extraire infos client depuis classification Mistral
    2. Créer client dans Supabase
    3. Créer structure dossiers Google Drive
    4. Récupérer template pièces selon type prêt
    5. Créer entrées pieces_dossier (statut=manquante)
    6. Logger l'activité
    7. Notifier courtier

    Args:
        courtier_id: ID du courtier
        email_data: Email parsé (dict)
        classification: Classification Mistral (dict)

    Returns:
        dict avec résultat

    Raises:
        ValueError: Si informations client manquantes
        RuntimeError: Si erreur création dossier
    """
    try:
        # Initialiser services
        drive = DriveManager()
        mistral = MistralService()

        # 1. Extraire infos client
        details = classification.get('details', {})
        client_nom = details.get('client_nom')
        client_prenom = details.get('client_prenom')
        client_email = details.get('client_email')
        type_pret = details.get('type_pret', 'immobilier')
        pieces_mentionnees = details.get('pieces_mentionnees', [])

        if not client_nom or not client_prenom:
            raise ValueError("Nom ou prénom client manquant dans classification")

        logger.info(
            "Création nouveau dossier",
            courtier_id=courtier_id,
            client_nom=client_nom,
            client_prenom=client_prenom,
            type_pret=type_pret
        )

        # 2. Récupérer courtier depuis DB
        courtier = get_courtier_by_id(UUID(courtier_id))
        if not courtier:
            raise ValueError(f"Courtier {courtier_id} non trouvé")
        
        courtier_nom = courtier.get('nom')
        courtier_prenom = courtier.get('prenom')

        # 3. Récupérer le dossier Drive du courtier
        # Le dossier_drive_id doit être valide car il est créé lors de la création du courtier
        courtier_folder_id = courtier.get('dossier_drive_id')
        
        if not courtier_folder_id:
            raise ValueError(
                f"Courtier {courtier_id} n'a pas de dossier_drive_id configuré. "
                "C'est une erreur critique : chaque courtier doit avoir un dossier Drive valide."
            )
        
        # Vérifier que le dossier existe sur Drive (erreur critique si invalide)
        # Utiliser list() au lieu de get() car cela fonctionne mieux avec les Shared Drives
        try:
            # Tester l'accès en essayant de lister le contenu (même si vide)
            query = f"'{courtier_folder_id}' in parents and trashed=false"
            drive.service.files().list(
                q=query,
                fields="files(id)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageSize=1
            ).execute()
            logger.info(
                "Dossier courtier validé",
                courtier_folder_id=courtier_folder_id
            )
        except Exception as e:
            raise RuntimeError(
                f"Dossier Drive du courtier {courtier_id} invalide ou inaccessible (ID: {courtier_folder_id}). "
                "Le dossier_drive_id doit pointer vers un dossier Google Drive valide et accessible. "
                "Vérifiez que le dossier existe et que le Service Account a les permissions nécessaires. "
                f"Erreur: {e}"
            ) from e

        # 4. Créer dossier client dans le dossier du courtier
        # Format: CLIENT_Nom_Prenom/
        client_folder_name = f"CLIENT_{client_nom}_{client_prenom}"
        
        # Créer dossier client
        client_folder_id = drive.get_or_create_folder(
            client_folder_name,
            courtier_folder_id
        )

        logger.info(
            "Dossier client créé sur Drive",
            courtier_folder_id=courtier_folder_id,
            client_folder_id=client_folder_id,
            client_folder_name=client_folder_name
        )

        # 5. TODO: Le client ne sera créé en DB que plus tard (quand on a plus d'infos)
        # Pour l'instant, on crée juste le dossier Drive

        # 6. Si courtier a mentionné des pièces spécifiques, on les structure
        # (Pour référence future, quand le client sera créé en DB)
        pieces_structurees = []
        if pieces_mentionnees:
            pieces_structurees = mistral.extract_pieces_from_text_sync(
                ', '.join(pieces_mentionnees)
            )
            logger.info(
                "Pièces structurées extraites (pour référence future)",
                nb_pieces=len(pieces_structurees),
                pieces=[p.get('nom_piece') for p in pieces_structurees]
            )

        # 10. TODO Session 7: Notifier courtier
        # notif.send_email(
        #     to=courtier.email,
        #     subject=f"✅ Dossier créé : {client_prenom} {client_nom}",
        #     body=f"""..."""
        # )

        logger.info(
            "Dossier Drive créé avec succès",
            client_nom=f"{client_prenom} {client_nom}",
            client_folder_id=client_folder_id,
            courtier_folder_id=courtier_folder_id,
            type_pret=type_pret
        )

        return {
            "status": "success",
            "client_nom": f"{client_prenom} {client_nom}",
            "client_folder_id": client_folder_id,
            "courtier_folder_id": courtier_folder_id,
            "type_pret": type_pret,
            "pieces_mentionnees": [p.get('nom_piece') for p in pieces_structurees] if pieces_structurees else []
        }

    except Exception as e:
        logger.error(
            "Erreur création dossier",
            error=str(e),
            courtier_id=courtier_id,
            exc_info=True
        )

        # TODO Session 7: Notifier courtier de l'erreur
        # try:
        #     courtier = db.get_courtier(courtier_id)
        #     notif.send_email(
        #         to=courtier.email,
        #         subject="❌ Erreur création dossier",
        #         body=f"Une erreur est survenue.\n\nErreur : {str(e)}"
        #     )
        # except:
        #     pass

        raise


def process_envoi_documents(
    courtier_id: str,
    email_data: dict,
    classification: dict
) -> dict:
    """
    Traite les documents envoyés par email (Job RQ).

    Étapes :
    1. Identifier le client (par email ou nom)
    2. Pour chaque pièce jointe :
       a. Télécharger
       b. Calculer hash (détecter doublons)
       c. Classifier avec Mistral Vision
       d. Convertir en PDF
       e. Compresser < 2 Mo
       f. Vérifier si fusion nécessaire (recto/verso)
       g. Upload Google Drive
       h. MAJ pieces_dossier
    3. Logger activité
    4. Notifier courtier

    Args:
        courtier_id: ID du courtier
        email_data: Email parsé avec attachments
        classification: Classification Mistral

    Returns:
        dict avec résultat
    """
    try:
        # Initialiser services
        drive = DriveManager()
        mistral = MistralService()
        
        # TODO Session 7: Initialiser DB, DocumentProcessor, NotificationService
        # db = get_db()
        # doc_processor = DocumentProcessor()
        # notif = NotificationService()

        from_email = email_data.get('from_email')
        attachments = email_data.get('attachments', [])

        logger.info(
            "Traitement documents",
            courtier_id=courtier_id,
            from_email=from_email,
            nb_attachments=len(attachments)
        )

        # 1. TODO Session 7: Identifier client
        # client = None
        # if from_email:
        #     client = db.get_client_by_email(courtier_id, from_email)
        # 
        # if not client:
        #     details = classification.get('details', {})
        #     client_nom = details.get('client_nom')
        #     client_prenom = details.get('client_prenom')
        #     if client_nom:
        #         client = db.find_client_by_name(courtier_id, client_nom, client_prenom)
        #
        # if not client:
        #     logger.warning("Client non identifié pour envoi documents")
        #     # Notifier courtier
        #     return {"status": "client_not_found"}

        # Placeholder pour le test
        client_folder_id = drive.master_folder_id
        client_nom = "TestClient"

        # 2. Traiter chaque pièce jointe
        pieces_traitees = []
        pieces_non_reconnues = []

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            for i, attachment in enumerate(attachments):
                try:
                    filename = attachment.get('filename', f'attachment_{i}')
                    # Pydantic serialise les bytes en base64 avec mode='json'
                    # Le champ garde son nom 'content' mais est encodé en base64
                    content_base64 = attachment.get('content')

                    if not content_base64:
                        logger.warning(f"Pièce jointe sans contenu: {filename}")
                        continue

                    # a. Télécharger
                    attachment_path = tmp_path / filename
                    with open(attachment_path, 'wb') as f:
                        f.write(base64.b64decode(content_base64))

                    # b. Hash (doublon ?)
                    file_hash = calculate_file_hash(attachment_path)

                    # TODO Session 7: Vérifier doublon en DB
                    # existing = db.get_piece_by_hash(client.id, file_hash)
                    # if existing:
                    #     logger.info("Document doublon détecté", filename=filename)
                    #     continue

                    # c. TODO Session 4: Classifier avec Mistral Vision
                    # doc_classification = await mistral.classify_document(...)

                    # d. TODO Session 4: Convertir PDF
                    # e. TODO Session 4: Compresser
                    # f. TODO Session 4: Fusion recto/verso si nécessaire

                    # g. Upload Drive (pour le test, upload simple)
                    file_id = drive.upload_file(
                        attachment_path,
                        client_folder_id,
                        filename
                    )

                    # h. TODO Session 7: MAJ pieces_dossier en DB

                    pieces_traitees.append({
                        'filename': filename,
                        'file_id': file_id,
                        'file_hash': file_hash
                    })

                    logger.info(
                        "Document traité",
                        filename=filename,
                        file_id=file_id
                    )

                except Exception as e:
                    logger.error(
                        "Erreur traitement pièce jointe",
                        filename=filename,
                        error=str(e),
                        exc_info=True
                    )
                    pieces_non_reconnues.append(filename)

        # 3. TODO Session 7: Logger
        # db.create_log({...})

        # 4. TODO Session 7: Notifier courtier

        logger.info(
            "Documents traités",
            nb_traites=len(pieces_traitees),
            nb_non_reconnus=len(pieces_non_reconnues)
        )

        return {
            "status": "success",
            "pieces_traitees": len(pieces_traitees),
            "pieces_non_reconnues": len(pieces_non_reconnues),
            "pieces": pieces_traitees
        }

    except Exception as e:
        logger.error(
            "Erreur traitement documents",
            error=str(e),
            exc_info=True
        )
        raise


def process_modifier_liste(
    courtier_id: str,
    email_data: dict,
    classification: dict
) -> dict:
    """
    Modifie la liste des pièces attendues pour un client (Job RQ).

    Étapes :
    1. Identifier le client
    2. Extraire pièces à ajouter/retirer depuis classification
    3. Structurer avec Mistral
    4. Ajouter nouvelles pièces en DB
    5. Retirer pièces si demandé
    6. Logger
    7. Notifier courtier

    Args:
        courtier_id: ID du courtier
        email_data: Email
        classification: Classification Mistral

    Returns:
        dict avec résultat
    """
    try:
        # Initialiser services
        mistral = MistralService()
        
        # TODO Session 7: Initialiser DB et NotificationService
        # db = get_db()
        # notif = NotificationService()

        details = classification.get('details', {})
        client_nom = details.get('client_nom')
        pieces_a_ajouter = details.get('pieces_a_ajouter', [])
        pieces_a_retirer = details.get('pieces_a_retirer', [])

        logger.info(
            "Modification liste pièces",
            courtier_id=courtier_id,
            client_nom=client_nom,
            nb_a_ajouter=len(pieces_a_ajouter),
            nb_a_retirer=len(pieces_a_retirer)
        )

        # 1. TODO Session 7: Identifier client
        # client = db.find_client_by_name(courtier_id, client_nom)
        # if not client:
        #     logger.warning("Client non trouvé pour modification liste")
        #     return {"status": "client_not_found"}

        # 2. Structurer pièces à ajouter
        pieces_ajoutees = []
        if pieces_a_ajouter:
            pieces_structurees = mistral.extract_pieces_from_text_sync(
                ', '.join(pieces_a_ajouter)
            )

            logger.info(
                "Pièces structurées",
                nb_pieces=len(pieces_structurees)
            )

            # TODO Session 7: Créer en DB
            # for piece in pieces_structurees:
            #     existing = db.get_type_piece_by_name(piece['nom_piece'])
            #     if not existing:
            #         type_piece = db.create_type_piece_custom(piece)
            #     else:
            #         type_piece = existing
            #     
            #     db.create_piece_dossier({
            #         'client_id': client.id,
            #         'type_piece_id': type_piece['id'],
            #         'statut': 'manquante'
            #     })
            #     
            #     pieces_ajoutees.append(piece['nom_piece'])

            pieces_ajoutees = [p['nom_piece'] for p in pieces_structurees]

        # 3. Retirer pièces
        pieces_retirees = []
        if pieces_a_retirer:
            # TODO Session 7: Supprimer de DB
            # for piece_nom in pieces_a_retirer:
            #     type_piece = db.get_type_piece_by_name(piece_nom)
            #     if type_piece:
            #         db.delete_piece_dossier(client.id, type_piece['id'])
            #         pieces_retirees.append(piece_nom)
            
            pieces_retirees = pieces_a_retirer

        # 4. TODO Session 7: Logger
        # db.create_log({...})

        # 5. TODO Session 7: Notifier courtier

        logger.info(
            "Liste pièces modifiée",
            pieces_ajoutees=pieces_ajoutees,
            pieces_retirees=pieces_retirees
        )

        return {
            "status": "success",
            "pieces_ajoutees": len(pieces_ajoutees),
            "pieces_retirees": len(pieces_retirees),
            "ajoutees": pieces_ajoutees,
            "retirees": pieces_retirees
        }

    except Exception as e:
        logger.error(
            "Erreur modification liste",
            error=str(e),
            exc_info=True
        )
        raise


# =============================================================================
# HELPERS
# =============================================================================

def calculate_file_hash(file_path: Path) -> str:
    """
    Calcule le hash SHA256 d'un fichier.

    Args:
        file_path: Chemin vers le fichier

    Returns:
        Hash SHA256 en hexadécimal
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
