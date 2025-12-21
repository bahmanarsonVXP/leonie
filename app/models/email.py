"""
Modèles Pydantic pour les emails et pièces jointes.

Ce module définit les schémas de données pour le traitement
des emails reçus via IMAP.
"""

import base64
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_serializer


class EmailAttachment(BaseModel):
    """Pièce jointe d'un email."""

    filename: str = Field(..., description="Nom du fichier")
    content_type: str = Field(..., description="Type MIME du fichier")
    size_bytes: int = Field(..., ge=0, description="Taille en octets")
    content: Optional[bytes] = Field(None, description="Contenu binaire du fichier")

    @field_serializer('content', when_used='json')
    def serialize_content(self, content: Optional[bytes]) -> Optional[str]:
        """
        Sérialise le contenu binaire en base64 pour JSON.

        Nécessaire pour envoyer les pièces jointes via Redis/RQ qui
        nécessite une sérialisation JSON.
        """
        if content is None:
            return None
        return base64.b64encode(content).decode('ascii')

    model_config = {
        "json_schema_extra": {
            "example": {
                "filename": "CNI_recto_verso.pdf",
                "content_type": "application/pdf",
                "size_bytes": 245678,
                "content": None  # Binary content not shown in example
            }
        }
    }


class EmailData(BaseModel):
    """Données d'un email reçu."""

    message_id: str = Field(..., description="ID unique du message email")
    from_address: EmailStr = Field(..., description="Adresse email de l'expéditeur")
    from_name: Optional[str] = Field(None, description="Nom de l'expéditeur")
    to_addresses: List[EmailStr] = Field(
        default_factory=list,
        description="Adresses email des destinataires"
    )
    cc_addresses: List[EmailStr] = Field(
        default_factory=list,
        description="Adresses email en copie"
    )
    subject: str = Field(..., description="Sujet de l'email")
    body_text: Optional[str] = Field(None, description="Corps de l'email en texte brut")
    body_html: Optional[str] = Field(None, description="Corps de l'email en HTML")
    date: datetime = Field(..., description="Date d'envoi de l'email")
    attachments: List[EmailAttachment] = Field(
        default_factory=list,
        description="Pièces jointes de l'email"
    )
    is_read: bool = Field(default=False, description="Email déjà lu")
    folder: str = Field(default="INBOX", description="Dossier IMAP de l'email")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message_id": "<abc123@gmail.com>",
                "from_address": "sophie.martin@email.com",
                "from_name": "Sophie Martin",
                "to_addresses": ["leonie@voxperience.com"],
                "cc_addresses": [],
                "subject": "Documents prêt immobilier",
                "body_text": "Bonjour, voici mes documents pour le dossier de prêt.",
                "body_html": "<p>Bonjour, voici mes documents pour le dossier de prêt.</p>",
                "date": "2024-01-22T09:30:00Z",
                "attachments": [
                    {
                        "filename": "CNI_recto_verso.pdf",
                        "content_type": "application/pdf",
                        "size_bytes": 245678
                    }
                ],
                "is_read": False,
                "folder": "INBOX"
            }
        }
    }


class EmailProcessingResult(BaseModel):
    """Résultat du traitement d'un email."""

    email_message_id: str = Field(..., description="ID du message traité")
    client_id: Optional[str] = Field(None, description="ID du client identifié")
    courtier_id: Optional[str] = Field(None, description="ID du courtier associé")
    pieces_traitees: int = Field(
        default=0,
        ge=0,
        description="Nombre de pièces jointes traitées"
    )
    pieces_classees: int = Field(
        default=0,
        ge=0,
        description="Nombre de pièces correctement classées"
    )
    pieces_non_reconnues: int = Field(
        default=0,
        ge=0,
        description="Nombre de pièces non reconnues"
    )
    erreurs: List[str] = Field(
        default_factory=list,
        description="Liste des erreurs rencontrées"
    )
    traite_a: datetime = Field(
        default_factory=datetime.utcnow,
        description="Date et heure du traitement"
    )
    success: bool = Field(..., description="Traitement réussi")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email_message_id": "<abc123@gmail.com>",
                "client_id": "456e7890-e89b-12d3-a456-426614174111",
                "courtier_id": "123e4567-e89b-12d3-a456-426614174000",
                "pieces_traitees": 3,
                "pieces_classees": 2,
                "pieces_non_reconnues": 1,
                "erreurs": [],
                "traite_a": "2024-01-22T09:35:00Z",
                "success": True
            }
        }
    }


class EmailAction(str, Enum):
    """
    Type d'action détectée dans un email.

    Classification Mistral des emails reçus pour déterminer
    le workflow de traitement approprié.
    """

    NOUVEAU_DOSSIER = "NOUVEAU_DOSSIER"
    """Initialisation d'un nouveau dossier client"""

    ENVOI_DOCUMENTS = "ENVOI_DOCUMENTS"
    """Envoi de documents pour un dossier existant"""

    MODIFIER_LISTE = "MODIFIER_LISTE"
    """Modification de la liste des pièces attendues"""

    QUESTION = "QUESTION"
    """Question du courtier nécessitant une réponse"""

    CONTEXTE = "CONTEXTE"
    """Email contextuel à archiver (copie pour info, etc.)"""


class EmailClassification(BaseModel):
    """
    Classification d'un email par Mistral AI.

    Détermine l'action à effectuer et extrait les informations
    pertinentes pour le traitement.
    """

    action: EmailAction = Field(..., description="Type d'action détectée")

    resume: str = Field(
        ...,
        max_length=200,
        description="Résumé court du message"
    )

    confiance: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Niveau de confiance de la classification (0.0 à 1.0)"
    )

    details: Dict = Field(
        default_factory=dict,
        description="Détails spécifiques selon l'action"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "action": "NOUVEAU_DOSSIER",
                    "resume": "Nouveau dossier prêt immobilier pour Sophie Martin",
                    "confiance": 0.95,
                    "details": {
                        "client_nom": "Martin",
                        "client_prenom": "Sophie",
                        "client_email": "sophie.martin@email.com",
                        "type_pret": "immobilier",
                        "pieces_mentionnees": ["CNI", "justificatifs de revenus"]
                    }
                },
                {
                    "action": "ENVOI_DOCUMENTS",
                    "resume": "Envoi de 3 documents pour le dossier Martin",
                    "confiance": 0.98,
                    "details": {
                        "nombre_pieces": 3,
                        "types_detectes": ["CNI", "bulletin de salaire", "avis d'imposition"]
                    }
                },
                {
                    "action": "MODIFIER_LISTE",
                    "resume": "Ajout de pièces spécifiques au dossier Dupont",
                    "confiance": 0.87,
                    "details": {
                        "client_nom": "Dupont",
                        "pieces_a_ajouter": ["attestation employeur", "RIB"],
                        "pieces_a_retirer": []
                    }
                },
                {
                    "action": "QUESTION",
                    "resume": "Question sur le traitement d'un document",
                    "confiance": 0.92,
                    "details": {
                        "sujet": "Document non reconnu",
                        "urgent": False
                    }
                },
                {
                    "action": "CONTEXTE",
                    "resume": "Email de suivi en copie",
                    "confiance": 0.89,
                    "details": {
                        "categorie": "suivi_client"
                    }
                }
            ]
        }
    }
