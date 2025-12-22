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
from app.services.client_identifier import ClientIdentifier

# Models
from app.models.email import EmailData

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

        # 1. Récupérer courtier depuis DB
        courtier = get_courtier_by_id(UUID(courtier_id))
        if not courtier:
            raise ValueError(f"Courtier {courtier_id} non trouvé")

        logger.info(
            "Création nouveau dossier",
            courtier_id=courtier_id,
            courtier_nom=f"{courtier.get('prenom')} {courtier.get('nom')}"
        )

        # 2. Convertir email_data en EmailData pour ClientIdentifier
        email = EmailData(**email_data)

        # 3. Vérifier si le client existe déjà
        existing_client = ClientIdentifier.identify_client_from_email(email, courtier)

        if existing_client:
            logger.warning(
                "Client existe déjà, dossier non recréé",
                client_id=existing_client.get('id'),
                client_nom=f"{existing_client.get('prenom')} {existing_client.get('nom')}"
            )
            return {
                "status": "exists",
                "client_id": existing_client.get('id'),
                "client_nom": f"{existing_client.get('prenom')} {existing_client.get('nom')}",
                "message": "Le client existe déjà en base de données"
            }

        # 4. Créer automatiquement le client avec dossier Drive
        logger.info("Client non trouvé, création automatique...")

        client = ClientIdentifier.create_client_from_email_and_classification(
            email,
            courtier,
            classification,
            drive
        )

        logger.info(
            "Client créé avec succès",
            client_id=client.get('id'),
            client_nom=f"{client.get('prenom')} {client.get('nom')}",
            dossier_drive_id=client.get('dossier_drive_id')
        )

        # 5. Extraire et structurer pièces mentionnées si disponibles
        details = classification.get('details', {})
        pieces_mentionnees = details.get('pieces_mentionnees', [])
        pieces_structurees = []

        if pieces_mentionnees:
            pieces_structurees = mistral.extract_pieces_from_text_sync(
                ', '.join(pieces_mentionnees)
            )
            logger.info(
                "Pièces structurées extraites",
                nb_pieces=len(pieces_structurees),
                pieces=[p.get('nom_piece') for p in pieces_structurees]
            )

        # 6. TODO Session 7+: Créer pieces_dossier en DB
        # for piece in pieces_structurees:
        #     db.create_piece_dossier({
        #         'client_id': client['id'],
        #         'type_piece_id': piece['type_piece_id'],
        #         'statut': 'manquante'
        #     })

        # 7. TODO Session 7: Notifier courtier
        # notif.send_email(
        #     to=courtier['email'],
        #     subject=f"✅ Dossier créé : {client['prenom']} {client['nom']}",
        #     body=f"""..."""
        # )

        return {
            "status": "success",
            "client_id": client.get('id'),
            "client_nom": f"{client.get('prenom')} {client.get('nom')}",
            "client_folder_id": client.get('dossier_drive_id'),
            "type_pret": client.get('type_pret'),
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

        # 1. Récupérer courtier depuis DB
        courtier = get_courtier_by_id(UUID(courtier_id))
        if not courtier:
            raise ValueError(f"Courtier {courtier_id} non trouvé")

        # 2. Convertir email_data en EmailData pour ClientIdentifier
        email = EmailData(**email_data)
        attachments = email_data.get('attachments', [])

        logger.info(
            "Traitement documents",
            courtier_id=courtier_id,
            courtier_nom=f"{courtier.get('prenom')} {courtier.get('nom')}",
            nb_attachments=len(attachments)
        )

        # 3. Identifier client (avec extraction emails avancée pour forwards)
        client = ClientIdentifier.identify_client_from_email(email, courtier)

        # 4. Si client non trouvé, créer automatiquement
        if not client:
            logger.info("Client non trouvé, création automatique depuis classification...")

            try:
                client = ClientIdentifier.create_client_from_email_and_classification(
                    email,
                    courtier,
                    classification,
                    drive
                )

                logger.info(
                    "Client créé automatiquement pour envoi documents",
                    client_id=client.get('id'),
                    client_nom=f"{client.get('prenom')} {client.get('nom')}"
                )
            except ValueError as e:
                logger.error(
                    "Impossible de créer le client automatiquement",
                    error=str(e)
                )
                # TODO Session 7+: Notifier courtier pour clarification
                return {
                    "status": "client_not_identified",
                    "message": "Impossible d'identifier ou créer le client",
                    "error": str(e)
                }

        # 5. Utiliser le dossier Drive du client
        client_folder_id = client.get('dossier_drive_id')
        client_nom = f"{client.get('prenom')} {client.get('nom')}"

        logger.info(
            "Client identifié pour documents",
            client_id=client.get('id'),
            client_nom=client_nom,
            dossier_drive_id=client_folder_id
        )

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
            client_id=client.get('id'),
            client_nom=client_nom,
            nb_traites=len(pieces_traitees),
            nb_non_reconnus=len(pieces_non_reconnues)
        )

        return {
            "status": "success",
            "client_id": client.get('id'),
            "client_nom": client_nom,
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
        drive = DriveManager()

        # 1. Récupérer courtier depuis DB
        courtier = get_courtier_by_id(UUID(courtier_id))
        if not courtier:
            raise ValueError(f"Courtier {courtier_id} non trouvé")

        # 2. Convertir email_data en EmailData pour ClientIdentifier
        email = EmailData(**email_data)

        details = classification.get('details', {})
        client_nom = details.get('client_nom')
        client_prenom = details.get('client_prenom')
        pieces_a_ajouter = details.get('pieces_a_ajouter', [])
        pieces_a_retirer = details.get('pieces_a_retirer', [])

        logger.info(
            "Modification liste pièces",
            courtier_id=courtier_id,
            client_nom=client_nom,
            client_prenom=client_prenom,
            nb_a_ajouter=len(pieces_a_ajouter),
            nb_a_retirer=len(pieces_a_retirer)
        )

        # 3. Identifier client (avec extraction emails avancée pour forwards)
        client = ClientIdentifier.identify_client_from_email(email, courtier)

        # 4. Si client non trouvé par email, chercher par nom
        if not client and client_nom:
            logger.info("Recherche client par nom...", nom=client_nom, prenom=client_prenom)
            client = find_client_by_name(
                UUID(courtier_id),
                client_nom,
                client_prenom
            )

            if client:
                logger.info(
                    "Client trouvé par nom",
                    client_id=client.get('id'),
                    client_nom=f"{client.get('prenom')} {client.get('nom')}"
                )

        # 5. Si toujours pas trouvé, créer automatiquement
        if not client:
            logger.info("Client non trouvé, création automatique...")

            try:
                client = ClientIdentifier.create_client_from_email_and_classification(
                    email,
                    courtier,
                    classification,
                    drive
                )

                logger.info(
                    "Client créé automatiquement pour modification liste",
                    client_id=client.get('id'),
                    client_nom=f"{client.get('prenom')} {client.get('nom')}"
                )
            except ValueError as e:
                logger.error(
                    "Impossible de créer le client automatiquement",
                    error=str(e)
                )
                # TODO Session 7+: Notifier courtier pour clarification
                return {
                    "status": "client_not_identified",
                    "message": "Impossible d'identifier ou créer le client",
                    "error": str(e)
                }

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
            client_id=client.get('id'),
            client_nom=f"{client.get('prenom')} {client.get('nom')}",
            pieces_ajoutees=pieces_ajoutees,
            pieces_retirees=pieces_retirees
        )

        return {
            "status": "success",
            "client_id": client.get('id'),
            "client_nom": f"{client.get('prenom')} {client.get('nom')}",
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
