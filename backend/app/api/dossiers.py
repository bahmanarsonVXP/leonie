"""
Endpoints API pour la gestion des dossiers clients.

Ce module fournit les endpoints REST pour:
- Lister les dossiers d'un courtier (avec filtres)
- Consulter les détails d'un dossier
- Voir les pièces d'un dossier
- Marquer un dossier comme complété

Authentification: JWT Supabase obligatoire
Accès: Courtier ne voit que ses propres dossiers
"""

from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.middleware.auth import AuthUser, get_current_user
from app.services.drive import DriveManager
from app.services.report import ReportGenerator
from app.utils.db import (
    get_client_by_id,
    get_clients_by_courtier,
    get_pieces_dossier,
    get_type_piece,
    log_activity,
    update_client,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/dossiers", tags=["dossiers"])


# =============================================================================
# MODÈLES PYDANTIC
# =============================================================================


class DossierSummary(BaseModel):
    """Résumé d'un dossier pour liste."""
    id: str
    nom: str
    prenom: str
    email_principal: str
    type_pret: str
    statut: str
    created_at: str
    updated_at: str
    nb_pieces_total: int = 0
    nb_pieces_recues: int = 0
    pourcentage_completion: float = 0.0


class PieceDetail(BaseModel):
    """Détail d'une pièce."""
    id: str
    type_piece_id: Optional[str] = None
    type_piece_nom: Optional[str] = None
    statut: str
    date_reception: Optional[str] = None
    fichier_drive_id: Optional[str] = None
    fichier_nom: Optional[str] = None
    commentaire: Optional[str] = None
    created_at: str
    updated_at: str


class DossierDetail(BaseModel):
    """Détail complet d'un dossier."""
    id: str
    nom: str
    prenom: str
    email_principal: str
    emails_secondaires: Optional[List[str]] = []
    type_pret: str
    statut: str
    dossier_drive_id: Optional[str] = None
    rapport_url: Optional[str] = None
    created_at: str
    updated_at: str
    pieces: List[PieceDetail] = []
    nb_pieces_total: int = 0
    nb_pieces_recues: int = 0
    nb_pieces_manquantes: int = 0
    nb_pieces_non_conformes: int = 0
    pourcentage_completion: float = 0.0


class DossierUpdateRequest(BaseModel):
    """Requête de mise à jour d'un dossier."""
    statut: Optional[str] = Field(None, description="Nouveau statut (en_cours, termine, annule)")


class DossierValidateRequest(BaseModel):
    """Requête de validation d'un dossier."""
    generer_rapport: bool = Field(True, description="Générer le rapport Word de suivi")


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/", response_model=List[DossierSummary])
async def list_dossiers(
    statut: Optional[str] = Query(None, description="Filtrer par statut (en_cours, termine, annule)"),
    user: AuthUser = Depends(get_current_user)
):
    """
    Liste les dossiers du courtier authentifié.

    Pour les admins : retourne TOUS les dossiers de TOUS les courtiers.
    Pour les courtiers : retourne seulement leurs dossiers.

    Filtres disponibles:
    - statut: Filtrer par statut (en_cours, termine, annule)

    Returns:
        Liste des dossiers (résumés)
    """
    try:
        courtier_id = user.courtier_id

        # Si admin (pas de courtier_id), récupérer TOUS les clients
        if not courtier_id:
            if user.is_admin:
                logger.info(
                    "Récupération liste TOUS dossiers (admin)",
                    admin_email=user.email,
                    statut_filtre=statut
                )
                # Récupérer tous les clients (tous courtiers)
                from app.utils.db import get_db
                db = get_db()
                query = db.table("clients").select("*")
                if statut:
                    query = query.eq("statut", statut)
                response = query.order("created_at", desc=True).execute()
                clients = response.data
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Courtier non associé à cet utilisateur"
                )
        else:
            logger.info(
                "Récupération liste dossiers",
                courtier_id=str(courtier_id),
                statut_filtre=statut
            )
            # Récupérer clients du courtier
            clients = get_clients_by_courtier(courtier_id, statut)

        # Transformer en résumés
        dossiers = []

        for client in clients:
            # Calculer stats pièces
            pieces = get_pieces_dossier(UUID(client.get('id')))

            nb_total = len(pieces)
            nb_recues = sum(1 for p in pieces if p.get('statut') == 'recue')
            pourcentage = round((nb_recues / nb_total) * 100, 1) if nb_total > 0 else 0

            dossiers.append(DossierSummary(
                id=client.get('id'),
                nom=client.get('nom'),
                prenom=client.get('prenom', ''),
                email_principal=client.get('email_principal'),
                type_pret=client.get('type_pret'),
                statut=client.get('statut'),
                created_at=client.get('created_at'),
                updated_at=client.get('updated_at'),
                nb_pieces_total=nb_total,
                nb_pieces_recues=nb_recues,
                pourcentage_completion=pourcentage
            ))

        logger.info(
            "Dossiers récupérés",
            courtier_id=str(courtier_id),
            nb_dossiers=len(dossiers)
        )

        return dossiers

    except Exception as e:
        logger.error(
            "Erreur récupération dossiers",
            courtier_id=str(user.courtier_id) if user.courtier_id else None,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des dossiers"
        )


@router.get("/{dossier_id}", response_model=DossierDetail)
async def get_dossier(
    dossier_id: UUID,
    user: AuthUser = Depends(get_current_user)
):
    """
    Récupère les détails complets d'un dossier.

    Inclut:
    - Informations client
    - Liste des pièces avec détails
    - Statistiques de complétion

    Args:
        dossier_id: ID du dossier (client)

    Returns:
        Détails complets du dossier
    """
    try:
        # Récupérer client
        client = get_client_by_id(dossier_id)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dossier non trouvé"
            )

        # Vérifier que le client appartient au courtier (sauf si admin)
        if not user.is_admin and str(client.get('courtier_id')) != str(user.courtier_id):
            logger.warning(
                "Tentative d'accès dossier d'un autre courtier",
                courtier_id=str(user.courtier_id),
                client_courtier_id=client.get('courtier_id'),
                dossier_id=str(dossier_id)
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé à ce dossier"
            )

        # Récupérer pièces
        pieces_raw = get_pieces_dossier(dossier_id)

        # Récupérer DriveManager pour les liens
        drive = DriveManager()

        # Transformer en modèles
        pieces = []
        nb_recues = 0
        nb_manquantes = 0
        nb_non_conformes = 0

        for piece in pieces_raw:
            type_piece = piece.get('types_pieces', {})
            type_piece_id = piece.get('type_piece_id')

            # Récupérer nom pièce si pas dans jointure
            type_piece_nom = type_piece.get('nom') if type_piece else None
            if not type_piece_nom and type_piece_id:
                type_piece_data = get_type_piece(UUID(type_piece_id))
                type_piece_nom = type_piece_data.get('nom') if type_piece_data else None

            piece_detail = PieceDetail(
                id=piece.get('id'),
                type_piece_id=type_piece_id,
                type_piece_nom=type_piece_nom,
                statut=piece.get('statut'),
                date_reception=piece.get('date_reception'),
                fichier_drive_id=piece.get('fichier_drive_id'),
                fichier_nom=piece.get('fichier_nom'),
                commentaire=piece.get('commentaire'),
                created_at=piece.get('created_at'),
                updated_at=piece.get('updated_at')
            )

            pieces.append(piece_detail)

            # Compter statuts
            statut = piece.get('statut')
            if statut == 'recue':
                nb_recues += 1
            elif statut == 'manquante':
                nb_manquantes += 1
            elif statut in ['non_conforme', 'non_reconnu']:
                nb_non_conformes += 1

        nb_total = len(pieces)
        pourcentage = round((nb_recues / nb_total) * 100, 1) if nb_total > 0 else 0

        # Récupérer lien rapport si disponible
        rapport_url = None
        dossier_drive_id = client.get('dossier_drive_id')
        if dossier_drive_id:
            rapport_file_id = drive.find_file_by_name(
                "_RAPPORT_SUIVI.docx",
                dossier_drive_id
            )
            if rapport_file_id:
                rapport_url = drive.get_shareable_link(rapport_file_id)

        dossier = DossierDetail(
            id=client.get('id'),
            nom=client.get('nom'),
            prenom=client.get('prenom', ''),
            email_principal=client.get('email_principal'),
            emails_secondaires=client.get('emails_secondaires', []),
            type_pret=client.get('type_pret'),
            statut=client.get('statut'),
            dossier_drive_id=dossier_drive_id,
            rapport_url=rapport_url,
            created_at=client.get('created_at'),
            updated_at=client.get('updated_at'),
            pieces=pieces,
            nb_pieces_total=nb_total,
            nb_pieces_recues=nb_recues,
            nb_pieces_manquantes=nb_manquantes,
            nb_pieces_non_conformes=nb_non_conformes,
            pourcentage_completion=pourcentage
        )

        logger.info(
            "Détails dossier récupérés",
            dossier_id=str(dossier_id),
            courtier_id=str(user.courtier_id),
            nb_pieces=nb_total
        )

        return dossier

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Erreur récupération détails dossier",
            dossier_id=str(dossier_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du dossier"
        )


@router.patch("/{dossier_id}", response_model=DossierDetail)
async def update_dossier(
    dossier_id: UUID,
    data: DossierUpdateRequest,
    user: AuthUser = Depends(get_current_user)
):
    """
    Met à jour un dossier.

    Champs modifiables:
    - statut

    Args:
        dossier_id: ID du dossier
        data: Données à mettre à jour

    Returns:
        Dossier mis à jour
    """
    try:
        # Vérifier que le dossier appartient au courtier
        client = get_client_by_id(dossier_id)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dossier non trouvé"
            )

        if not user.is_admin and str(client.get('courtier_id')) != str(user.courtier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé à ce dossier"
            )

        # Construire updates
        updates = {}

        if data.statut:
            if data.statut not in ['en_cours', 'termine', 'annule']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Statut invalide. Valeurs acceptées: en_cours, termine, annule"
                )
            updates['statut'] = data.statut

        # Appliquer updates
        if updates:
            update_client(dossier_id, updates)
            logger.info(
                "Dossier mis à jour",
                dossier_id=str(dossier_id),
                updates=updates
            )

        # Retourner dossier mis à jour
        return await get_dossier(dossier_id, user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Erreur mise à jour dossier",
            dossier_id=str(dossier_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour du dossier"
        )


@router.post("/{dossier_id}/validate")
async def validate_dossier(
    dossier_id: UUID,
    data: DossierValidateRequest,
    user: AuthUser = Depends(get_current_user)
):
    """
    Marque un dossier comme terminé et génère le rapport de suivi.

    Args:
        dossier_id: ID du dossier
        data: Options de validation

    Returns:
        Détails du dossier validé + URL du rapport
    """
    try:
        # Vérifier que le dossier appartient au courtier
        client = get_client_by_id(dossier_id)

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dossier non trouvé"
            )

        if not user.is_admin and str(client.get('courtier_id')) != str(user.courtier_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé à ce dossier"
            )

        # Vérifier pièces obligatoires avant validation
        pieces = get_pieces_dossier(dossier_id)
        pieces_obligatoires_manquantes = []

        for piece in pieces:
            type_piece_id = piece.get('type_piece_id')
            if type_piece_id:
                type_piece = get_type_piece(UUID(type_piece_id))
                if type_piece and type_piece.get('obligatoire') and piece.get('statut') != 'recue':
                    pieces_obligatoires_manquantes.append(
                        type_piece.get('nom', 'Pièce inconnue')
                    )

        if pieces_obligatoires_manquantes:
            logger.warning(
                "Validation refusée: pièces obligatoires manquantes",
                dossier_id=str(dossier_id),
                pieces_manquantes=pieces_obligatoires_manquantes
            )
            return {
                "status": "error",
                "message": f"{len(pieces_obligatoires_manquantes)} pièce(s) obligatoire(s) manquante(s)",
                "pieces_manquantes": pieces_obligatoires_manquantes
            }

        # Marquer comme terminé
        update_client(dossier_id, {'statut': 'termine'})

        # Logger l'activité
        log_activity(
            action='dossier_valide',
            details={'validated_by': user.email},
            client_id=dossier_id,
            courtier_id=user.courtier_id
        )

        logger.info(
            "Dossier validé",
            dossier_id=str(dossier_id),
            courtier_id=str(user.courtier_id)
        )

        # Générer rapport si demandé
        rapport_file_id = None

        if data.generer_rapport:
            try:
                report_gen = ReportGenerator()
                rapport_file_id = report_gen.generate_client_report(
                    dossier_id,
                    upload_to_drive=True
                )

                logger.info(
                    "Rapport généré pour dossier validé",
                    dossier_id=str(dossier_id),
                    rapport_file_id=rapport_file_id
                )
            except Exception as e:
                logger.error(
                    "Erreur génération rapport validation",
                    dossier_id=str(dossier_id),
                    error=str(e),
                    exc_info=True
                )
                # Ne pas bloquer la validation si rapport échoue

        # Retourner dossier validé
        dossier_detail = await get_dossier(dossier_id, user)

        return {
            "status": "success",
            "message": "Dossier marqué comme terminé",
            "dossier": dossier_detail,
            "rapport_file_id": rapport_file_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Erreur validation dossier",
            dossier_id=str(dossier_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la validation du dossier"
        )
