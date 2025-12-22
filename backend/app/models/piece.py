"""
Modèles Pydantic pour les pièces justificatives.

Ce module définit les schémas de données pour les types de pièces
et les pièces reçues dans les dossiers clients.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StatutPiece(str, Enum):
    """Statut d'une pièce justificative."""

    MANQUANTE = "manquante"
    RECUE = "recue"
    NON_CONFORME = "non_conforme"
    NON_RECONNU = "non_reconnu"


class TypePieceBase(BaseModel):
    """Schéma de base pour un type de pièce."""

    type_pret: str = Field(
        ...,
        description="Type de prêt: immobilier, professionnel ou commun"
    )
    categorie: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Catégorie: identite, domicile, revenus, patrimoine, etc."
    )
    nom_piece: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nom du type de pièce"
    )
    description: Optional[str] = Field(
        None,
        description="Description détaillée de la pièce"
    )
    obligatoire: bool = Field(
        default=True,
        description="Pièce obligatoire ou optionnelle"
    )
    ordre: Optional[int] = Field(
        None,
        description="Ordre d'affichage"
    )
    regles_validation: Optional[Dict[str, Any]] = Field(
        None,
        description="Règles de validation JSON (durée validité, pages requises, etc.)"
    )


class TypePieceCreate(TypePieceBase):
    """Schéma pour la création d'un type de pièce."""

    pass


class TypePiece(TypePieceBase):
    """Schéma complet d'un type de pièce (lecture depuis DB)."""

    id: UUID = Field(..., description="Identifiant unique du type de pièce")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "789e0123-e89b-12d3-a456-426614174222",
                "type_pret": "immobilier",
                "categorie": "identite",
                "nom_piece": "Pièce d'identité",
                "description": "CNI recto-verso ou Passeport en cours de validité",
                "obligatoire": True,
                "ordre": 1,
                "regles_validation": {
                    "duree_validite_mois": 120,
                    "pages_requises": ["recto", "verso"]
                }
            }
        }
    }


class PieceDossierBase(BaseModel):
    """Schéma de base pour une pièce de dossier."""

    statut: StatutPiece = Field(
        default=StatutPiece.MANQUANTE,
        description="Statut de la pièce"
    )
    commentaire_conformite: Optional[str] = Field(
        None,
        description="Commentaire sur la conformité de la pièce"
    )


class PieceDossierCreate(PieceDossierBase):
    """Schéma pour la création d'une pièce de dossier."""

    client_id: UUID = Field(..., description="ID du client")
    type_piece_id: UUID = Field(..., description="ID du type de pièce")
    fichier_drive_id: Optional[str] = Field(
        None,
        description="ID du fichier sur Google Drive"
    )
    fichier_hash: Optional[str] = Field(
        None,
        description="Hash SHA256 du fichier pour détecter les doublons"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Métadonnées extraites du document"
    )


class PieceDossierUpdate(BaseModel):
    """Schéma pour la mise à jour d'une pièce de dossier."""

    type_piece_id: Optional[UUID] = Field(None, description="ID du type de pièce")
    statut: Optional[StatutPiece] = Field(None, description="Statut de la pièce")
    fichier_drive_id: Optional[str] = Field(
        None,
        description="ID du fichier sur Google Drive"
    )
    fichier_hash: Optional[str] = Field(
        None,
        description="Hash SHA256 du fichier"
    )
    commentaire_conformite: Optional[str] = Field(
        None,
        description="Commentaire sur la conformité"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Métadonnées extraites"
    )


class PieceDossier(PieceDossierBase):
    """Schéma complet d'une pièce de dossier (lecture depuis DB)."""

    id: UUID = Field(..., description="Identifiant unique de la pièce")
    client_id: UUID = Field(..., description="ID du client")
    type_piece_id: Optional[UUID] = Field(None, description="ID du type de pièce")
    fichier_drive_id: Optional[str] = Field(None, description="ID du fichier sur Drive")
    fichier_hash: Optional[str] = Field(None, description="Hash SHA256 du fichier")
    date_reception: Optional[datetime] = Field(None, description="Date de réception")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Métadonnées extraites")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de dernière mise à jour")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "abc1234-e89b-12d3-a456-426614174333",
                "client_id": "456e7890-e89b-12d3-a456-426614174111",
                "type_piece_id": "789e0123-e89b-12d3-a456-426614174222",
                "statut": "recue",
                "fichier_drive_id": "1DriveFileId123456",
                "fichier_hash": "a1b2c3d4e5f6...",
                "date_reception": "2024-01-22T10:15:00Z",
                "commentaire_conformite": "Document conforme",
                "metadata": {
                    "nom_fichier": "CNI_MARTIN_Sophie.pdf",
                    "date_validite": "2030-12-31",
                    "numero_document": "123456789"
                },
                "created_at": "2024-01-22T10:15:00Z",
                "updated_at": "2024-01-22T10:15:00Z"
            }
        }
    }


class PieceDossierWithType(PieceDossier):
    """Pièce de dossier enrichie avec les informations du type de pièce."""

    type_piece: Optional[TypePiece] = Field(
        None,
        description="Informations complètes sur le type de pièce"
    )

    model_config = {
        "from_attributes": True
    }
