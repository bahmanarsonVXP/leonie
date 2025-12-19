"""
Modèles Pydantic pour les courtiers.

Ce module définit les schémas de données pour les courtiers en prêts
immobiliers et professionnels.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class CourtierBase(BaseModel):
    """Schéma de base pour un courtier."""

    email: EmailStr = Field(..., description="Email professionnel du courtier")
    nom: str = Field(..., min_length=1, max_length=100, description="Nom du courtier")
    prenom: str = Field(..., min_length=1, max_length=100, description="Prénom du courtier")
    dossier_drive_id: str = Field(
        ...,
        description="ID du dossier racine Google Drive du courtier"
    )


class CourtierCreate(CourtierBase):
    """Schéma pour la création d'un courtier."""

    actif: bool = Field(default=True, description="Le courtier est actif")


class CourtierUpdate(BaseModel):
    """Schéma pour la mise à jour d'un courtier."""

    email: Optional[EmailStr] = Field(None, description="Email professionnel du courtier")
    nom: Optional[str] = Field(None, min_length=1, max_length=100, description="Nom du courtier")
    prenom: Optional[str] = Field(None, min_length=1, max_length=100, description="Prénom du courtier")
    dossier_drive_id: Optional[str] = Field(
        None,
        description="ID du dossier racine Google Drive du courtier"
    )
    actif: Optional[bool] = Field(None, description="Le courtier est actif")


class Courtier(CourtierBase):
    """Schéma complet d'un courtier (lecture depuis DB)."""

    id: UUID = Field(..., description="Identifiant unique du courtier")
    actif: bool = Field(..., description="Le courtier est actif")
    created_at: datetime = Field(..., description="Date de création")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "jean.dupont@courtage-exemple.fr",
                "nom": "Dupont",
                "prenom": "Jean",
                "dossier_drive_id": "1a2b3c4d5e6f7g8h9i0j",
                "actif": True,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    }
