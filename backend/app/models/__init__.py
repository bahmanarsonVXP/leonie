"""Modèles de données Pydantic pour Léonie."""

from app.models.courtier import Courtier, CourtierCreate, CourtierUpdate
from app.models.client import Client, ClientCreate, ClientUpdate, TypePret, StatutDossier
from app.models.piece import (
    TypePiece,
    TypePieceCreate,
    PieceDossier,
    PieceDossierCreate,
    PieceDossierUpdate,
    StatutPiece,
)
from app.models.email import EmailData, EmailAttachment

__all__ = [
    # Courtier
    "Courtier",
    "CourtierCreate",
    "CourtierUpdate",
    # Client
    "Client",
    "ClientCreate",
    "ClientUpdate",
    "TypePret",
    "StatutDossier",
    # Pièce
    "TypePiece",
    "TypePieceCreate",
    "PieceDossier",
    "PieceDossierCreate",
    "PieceDossierUpdate",
    "StatutPiece",
    # Email
    "EmailData",
    "EmailAttachment",
]
