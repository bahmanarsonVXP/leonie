"""
Endpoints API pour l'administration.

Ce module fournit les endpoints admin pour la gestion
des courtiers et de la configuration système.

Authentification: JWT Supabase obligatoire + rôle admin
Accès: Admin seulement (vérifié via email ou rôle)
"""

from typing import List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.middleware.auth import AuthUser, require_admin
from app.services.drive import DriveManager
from app.utils.db import (
    create_courtier,
    get_all_courtiers,
    get_courtier_by_id,
    update_courtier,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/admin", tags=["admin"])


# =============================================================================
# MODÈLES PYDANTIC
# =============================================================================


class CourtierCreateRequest(BaseModel):
    """Requête de création d'un courtier."""

    email: EmailStr = Field(..., description="Email professionnel du courtier")
    nom: str = Field(..., min_length=1, max_length=100, description="Nom du courtier")
    prenom: str = Field(..., min_length=1, max_length=100, description="Prénom du courtier")
    actif: bool = Field(default=True, description="Le courtier est actif")


class CourtierUpdateRequest(BaseModel):
    """Requête de mise à jour d'un courtier."""

    email: Optional[EmailStr] = Field(None, description="Email professionnel du courtier")
    nom: Optional[str] = Field(None, min_length=1, max_length=100, description="Nom du courtier")
    prenom: Optional[str] = Field(None, min_length=1, max_length=100, description="Prénom du courtier")
    actif: Optional[bool] = Field(None, description="Le courtier est actif")


class CourtierResponse(BaseModel):
    """Réponse avec données d'un courtier."""

    id: str
    email: str
    nom: str
    prenom: str
    dossier_drive_id: Optional[str] = None
    actif: bool
    created_at: str
    updated_at: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get("/courtiers", response_model=List[CourtierResponse])
async def list_courtiers(admin: AuthUser = Depends(require_admin)):
    """
    Liste tous les courtiers (admin seulement).

    Returns:
        Liste de tous les courtiers (actifs et inactifs)
    """
    try:
        logger.info("Récupération liste courtiers (admin)", admin_email=admin.email)

        courtiers = get_all_courtiers()

        response = []
        for courtier in courtiers:
            response.append(CourtierResponse(
                id=courtier.get('id'),
                email=courtier.get('email'),
                nom=courtier.get('nom'),
                prenom=courtier.get('prenom'),
                dossier_drive_id=courtier.get('dossier_drive_id'),
                actif=courtier.get('actif', True),
                created_at=courtier.get('created_at'),
                updated_at=courtier.get('updated_at')
            ))

        logger.info("Courtiers récupérés", nb_courtiers=len(response))
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Erreur récupération courtiers",
            admin_email=admin.email,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des courtiers"
        )


@router.post("/courtiers", response_model=CourtierResponse, status_code=status.HTTP_201_CREATED)
async def create_courtier(
    data: CourtierCreateRequest,
    admin: AuthUser = Depends(require_admin)
):
    """
    Crée un nouveau courtier (admin seulement).

    Étapes:
    1. Crée le dossier Drive du courtier
    2. Crée l'enregistrement en DB

    Args:
        data: Données du courtier à créer

    Returns:
        Courtier créé
    """
    try:
        logger.info(
            "Création courtier (admin)",
            admin_email=admin.email,
            courtier_email=data.email
        )

        # 1. Créer dossier Drive
        drive = DriveManager()
        folder_id = drive.create_courtier_folder(data.nom, data.prenom)

        logger.info(
            "Dossier Drive courtier créé",
            folder_id=folder_id,
            courtier_email=data.email
        )

        # 2. Créer en DB
        courtier_data = {
            'email': data.email,
            'nom': data.nom,
            'prenom': data.prenom,
            'dossier_drive_id': folder_id,
            'actif': data.actif
        }

        courtier = create_courtier(courtier_data)

        logger.info(
            "Courtier créé",
            courtier_id=courtier.get('id'),
            courtier_email=data.email
        )

        return CourtierResponse(
            id=courtier.get('id'),
            email=courtier.get('email'),
            nom=courtier.get('nom'),
            prenom=courtier.get('prenom'),
            dossier_drive_id=courtier.get('dossier_drive_id'),
            actif=courtier.get('actif', True),
            created_at=courtier.get('created_at'),
            updated_at=courtier.get('updated_at')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Erreur création courtier",
            admin_email=admin.email,
            courtier_email=data.email,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du courtier: {str(e)}"
        )


@router.get("/courtiers/{courtier_id}", response_model=CourtierResponse)
async def get_courtier(
    courtier_id: UUID,
    admin: AuthUser = Depends(require_admin)
):
    """
    Récupère les détails d'un courtier (admin seulement).

    Args:
        courtier_id: ID du courtier

    Returns:
        Détails du courtier
    """
    try:
        courtier = get_courtier_by_id(courtier_id)

        if not courtier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Courtier non trouvé"
            )

        return CourtierResponse(
            id=courtier.get('id'),
            email=courtier.get('email'),
            nom=courtier.get('nom'),
            prenom=courtier.get('prenom'),
            dossier_drive_id=courtier.get('dossier_drive_id'),
            actif=courtier.get('actif', True),
            created_at=courtier.get('created_at'),
            updated_at=courtier.get('updated_at')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Erreur récupération courtier",
            courtier_id=str(courtier_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du courtier"
        )


@router.patch("/courtiers/{courtier_id}", response_model=CourtierResponse)
async def update_courtier(
    courtier_id: UUID,
    data: CourtierUpdateRequest,
    admin: AuthUser = Depends(require_admin)
):
    """
    Met à jour un courtier (admin seulement).

    Args:
        courtier_id: ID du courtier
        data: Données à mettre à jour

    Returns:
        Courtier mis à jour
    """
    try:
        # Vérifier que le courtier existe
        courtier = get_courtier_by_id(courtier_id)

        if not courtier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Courtier non trouvé"
            )

        # Construire updates
        updates = {}

        if data.email is not None:
            updates['email'] = data.email
        if data.nom is not None:
            updates['nom'] = data.nom
        if data.prenom is not None:
            updates['prenom'] = data.prenom
        if data.actif is not None:
            updates['actif'] = data.actif

        # Appliquer updates
        if updates:
            courtier = update_courtier(courtier_id, updates)
            logger.info(
                "Courtier mis à jour",
                courtier_id=str(courtier_id),
                updates=updates
            )
        else:
            # Pas de changements
            courtier = get_courtier_by_id(courtier_id)

        return CourtierResponse(
            id=courtier.get('id'),
            email=courtier.get('email'),
            nom=courtier.get('nom'),
            prenom=courtier.get('prenom'),
            dossier_drive_id=courtier.get('dossier_drive_id'),
            actif=courtier.get('actif', True),
            created_at=courtier.get('created_at'),
            updated_at=courtier.get('updated_at')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Erreur mise à jour courtier",
            courtier_id=str(courtier_id),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour du courtier"
        )
