"""
Modèles Pydantic pour les clients (dossiers).

Ce module définit les schémas de données pour les dossiers clients
des courtiers.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class TypePret(str, Enum):
    """Type de prêt demandé par le client."""

    IMMOBILIER = "immobilier"
    PROFESSIONNEL = "professionnel"


class StatutDossier(str, Enum):
    """Statut d'avancement du dossier client."""

    EN_COURS = "en_cours"
    COMPLET = "complet"
    ARCHIVE = "archive"


class ClientBase(BaseModel):
    """Schéma de base pour un client."""

    nom: str = Field(..., min_length=1, max_length=100, description="Nom du client")
    prenom: str = Field(..., min_length=1, max_length=100, description="Prénom du client")
    email_principal: EmailStr = Field(..., description="Email principal du client")
    emails_secondaires: List[EmailStr] = Field(
        default_factory=list,
        description="Emails secondaires (conjoint, co-emprunteur, etc.)"
    )
    type_pret: TypePret = Field(..., description="Type de prêt: immobilier ou professionnel")


class ClientCreate(ClientBase):
    """Schéma pour la création d'un client."""

    courtier_id: UUID = Field(..., description="ID du courtier propriétaire")
    dossier_drive_id: str = Field(
        ...,
        description="ID du dossier Google Drive du client"
    )
    statut: StatutDossier = Field(
        default=StatutDossier.EN_COURS,
        description="Statut initial du dossier"
    )


class ClientUpdate(BaseModel):
    """Schéma pour la mise à jour d'un client."""

    nom: Optional[str] = Field(None, min_length=1, max_length=100, description="Nom du client")
    prenom: Optional[str] = Field(None, min_length=1, max_length=100, description="Prénom du client")
    email_principal: Optional[EmailStr] = Field(None, description="Email principal du client")
    emails_secondaires: Optional[List[EmailStr]] = Field(
        None,
        description="Emails secondaires (conjoint, co-emprunteur, etc.)"
    )
    type_pret: Optional[TypePret] = Field(None, description="Type de prêt")
    statut: Optional[StatutDossier] = Field(None, description="Statut du dossier")
    dossier_drive_id: Optional[str] = Field(
        None,
        description="ID du dossier Google Drive du client"
    )


class Client(ClientBase):
    """Schéma complet d'un client (lecture depuis DB)."""

    id: UUID = Field(..., description="Identifiant unique du client")
    courtier_id: UUID = Field(..., description="ID du courtier propriétaire")
    statut: StatutDossier = Field(..., description="Statut du dossier")
    dossier_drive_id: str = Field(..., description="ID du dossier Google Drive")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de dernière mise à jour")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "456e7890-e89b-12d3-a456-426614174111",
                "courtier_id": "123e4567-e89b-12d3-a456-426614174000",
                "nom": "Martin",
                "prenom": "Sophie",
                "email_principal": "sophie.martin@email.com",
                "emails_secondaires": ["pierre.martin@email.com"],
                "type_pret": "immobilier",
                "statut": "en_cours",
                "dossier_drive_id": "9z8y7x6w5v4u3t2s1r0q",
                "created_at": "2024-01-20T14:30:00Z",
                "updated_at": "2024-01-20T14:30:00Z"
            }
        }
    }


class ClientWithProgress(Client):
    """Client avec statistiques de progression du dossier."""

    total_pieces: int = Field(..., description="Nombre total de pièces attendues")
    pieces_recues: int = Field(..., description="Nombre de pièces reçues")
    pieces_conformes: int = Field(..., description="Nombre de pièces conformes")
    pieces_manquantes: int = Field(..., description="Nombre de pièces manquantes")
    pourcentage_completion: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Pourcentage de complétion du dossier"
    )

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "456e7890-e89b-12d3-a456-426614174111",
                "courtier_id": "123e4567-e89b-12d3-a456-426614174000",
                "nom": "Martin",
                "prenom": "Sophie",
                "email_principal": "sophie.martin@email.com",
                "emails_secondaires": ["pierre.martin@email.com"],
                "type_pret": "immobilier",
                "statut": "en_cours",
                "dossier_drive_id": "9z8y7x6w5v4u3t2s1r0q",
                "created_at": "2024-01-20T14:30:00Z",
                "updated_at": "2024-01-20T14:30:00Z",
                "total_pieces": 15,
                "pieces_recues": 10,
                "pieces_conformes": 8,
                "pieces_manquantes": 5,
                "pourcentage_completion": 66.67
            }
        }
    }
