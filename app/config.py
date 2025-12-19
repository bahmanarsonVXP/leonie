"""
Configuration de l'application avec pydantic-settings.

Ce module centralise toutes les variables d'environnement
et la configuration de l'application Léonie.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration de l'application.

    Toutes les variables d'environnement sont chargées depuis
    le fichier .env ou les variables d'environnement système.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # ==========================================================================
    # APPLICATION
    # ==========================================================================

    APP_NAME: str = Field(default="Léonie", description="Nom de l'application")
    APP_VERSION: str = Field(default="0.2.0", description="Version de l'application")
    ENVIRONMENT: str = Field(default="development", description="Environnement (development, staging, production)")
    DEBUG: bool = Field(default=False, description="Mode debug")
    LOG_LEVEL: str = Field(default="INFO", description="Niveau de log (DEBUG, INFO, WARNING, ERROR)")

    # ==========================================================================
    # SUPABASE
    # ==========================================================================

    SUPABASE_URL: str = Field(..., description="URL de votre projet Supabase")
    SUPABASE_KEY: str = Field(..., description="Clé API Supabase (anon/service_role)")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = Field(
        None,
        description="Clé service_role pour opérations admin"
    )

    # ==========================================================================
    # REDIS & WORKERS
    # ==========================================================================

    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="URL de connexion Redis"
    )

    # ==========================================================================
    # EMAIL (IMAP)
    # ==========================================================================

    IMAP_HOST: str = Field(default="imap.gmail.com", description="Serveur IMAP")
    IMAP_PORT: int = Field(default=993, description="Port IMAP")
    IMAP_EMAIL: str = Field(..., description="Email du compte IMAP (leonie@voxperience.com)")
    IMAP_PASSWORD: str = Field(..., description="Mot de passe ou App Password Gmail")
    IMAP_LABEL: str = Field(default="LEONIE", description="Label Gmail où arrivent les emails pour Léonie")
    EMAIL_POLLING_INTERVAL: int = Field(
        default=300,
        description="Intervalle de polling en secondes (5min par défaut)"
    )

    # ==========================================================================
    # EMAIL (SMTP - pour envoi notifications)
    # ==========================================================================

    SMTP_HOST: str = Field(default="smtp.gmail.com", description="Serveur SMTP")
    SMTP_PORT: int = Field(default=587, description="Port SMTP")
    SMTP_EMAIL: str = Field(..., description="Email d'envoi des notifications")
    SMTP_PASSWORD: str = Field(..., description="Mot de passe SMTP")
    SMTP_FROM_NAME: str = Field(default="Léonie", description="Nom de l'expéditeur")

    # ==========================================================================
    # MISTRAL AI
    # ==========================================================================

    MISTRAL_API_KEY: str = Field(..., description="Clé API Mistral AI")
    MISTRAL_MODEL_CHAT: str = Field(
        default="mistral-large-latest",
        description="Modèle Mistral pour classification (chat)"
    )
    MISTRAL_MODEL_VISION: str = Field(
        default="pixtral-large-latest",
        description="Modèle Mistral pour documents (vision)"
    )
    MISTRAL_MAX_TOKENS: int = Field(default=2000, description="Tokens max par requête")
    MISTRAL_TEMPERATURE: float = Field(default=0.1, description="Température (0-1)")

    # ==========================================================================
    # GOOGLE DRIVE
    # ==========================================================================

    GOOGLE_CREDENTIALS_FILE: str = Field(
        default="service-account.json",
        description="Chemin vers le fichier credentials Google Service Account"
    )
    GDRIVE_ROOT_FOLDER_ID: Optional[str] = Field(
        None,
        description="ID du dossier racine Google Drive (optionnel)"
    )

    # ==========================================================================
    # DOCUMENTS & FILES
    # ==========================================================================

    MAX_ATTACHMENT_SIZE_MB: int = Field(
        default=25,
        description="Taille max des pièces jointes en MB"
    )
    ALLOWED_EXTENSIONS: str = Field(
        default="pdf,jpg,jpeg,png,doc,docx,xls,xlsx,heic,tiff,webp",
        description="Extensions autorisées (séparées par virgules)"
    )
    UPLOAD_TEMP_DIR: str = Field(
        default="/tmp/leonie",
        description="Dossier temporaire pour uploads"
    )

    # Document Processing
    MAX_FILE_SIZE_MB: int = Field(
        default=10,
        description="Taille maximale d'un fichier pour le traitement de documents (MB)"
    )
    TARGET_PDF_SIZE_MB: float = Field(
        default=1.8,
        description="Taille cible pour la compression PDF (MB, <2MB pour Drive)"
    )
    DOCUMENT_TEMP_DIR: str = Field(
        default="/tmp/leonie/documents",
        description="Dossier temporaire pour le traitement de documents"
    )

    # ==========================================================================
    # RAPPORTS
    # ==========================================================================

    RAPPORT_QUOTIDIEN_HEURE: str = Field(
        default="08:00",
        description="Heure d'envoi du rapport quotidien (HH:MM)"
    )
    RAPPORT_TEMPLATE_PATH: str = Field(
        default="templates/rapport_template.docx",
        description="Chemin vers le template Word des rapports"
    )

    # ==========================================================================
    # SÉCURITÉ & API
    # ==========================================================================

    API_SECRET_KEY: str = Field(..., description="Clé secrète pour JWT et signing")
    API_ADMIN_TOKEN: Optional[str] = Field(
        None,
        description="Token d'admin pour endpoints protégés"
    )
    CORS_ORIGINS: str = Field(
        default="*",
        description="Origines CORS autorisées (séparées par virgules)"
    )

    # ==========================================================================
    # MÉTHODES HELPER
    # ==========================================================================

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Liste des extensions autorisées."""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def cors_origins_list(self) -> list[str]:
        """Liste des origines CORS."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        """Vérifie si on est en production."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Vérifie si on est en développement."""
        return self.ENVIRONMENT.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Récupère les settings de l'application (avec cache).

    Returns:
        Settings: Instance des settings de l'application.

    Example:
        >>> from app.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.SUPABASE_URL)
    """
    return Settings()
