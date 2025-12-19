"""
Léonie - Agent IA pour courtiers en prêts immobiliers et professionnels.

Point d'entrée de l'application FastAPI.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings

# Configuration du logging structuré avec structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

# Configuration du logging standard (fallback)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionnaire du cycle de vie de l'application.

    Gère le startup et shutdown de l'application.
    """
    # Startup
    settings = get_settings()
    logger.info(f"Démarrage de {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environnement: {settings.ENVIRONMENT}")

    # TODO: Initialiser les connexions (Supabase, Redis, etc.)
    # TODO: Lancer les workers si nécessaire

    yield

    # Shutdown
    logger.info("Arrêt de l'application...")
    # TODO: Fermer les connexions proprement


# Création de l'application FastAPI
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Agent IA pour courtiers en prêts immobiliers et professionnels",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# ROUTES DE BASE
# =============================================================================


@app.get("/", tags=["Health"])
async def root() -> Dict[str, str]:
    """
    Route racine de l'API.

    Returns:
        Dict avec un message de bienvenue.
    """
    return {
        "message": f"Bienvenue sur {settings.APP_NAME} v{settings.APP_VERSION}",
        "status": "running",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Endpoint de health check pour monitoring.

    Returns:
        Dict avec le statut de santé de l'application.
    """
    # TODO: Vérifier les connexions (Supabase, Redis, etc.)

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {
            "database": "ok",  # TODO: Vérifier Supabase
            "redis": "ok",     # TODO: Vérifier Redis
        }
    }


@app.get("/api/info", tags=["Info"])
async def api_info() -> Dict[str, Any]:
    """
    Informations sur l'API.

    Returns:
        Dict avec les informations de l'API.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "endpoints": {
            "docs": "/docs" if not settings.is_production else None,
            "redoc": "/redoc" if not settings.is_production else None,
            "health": "/health",
            "test_imap": "/test-imap",
            "test_mistral": "/test-mistral",
            "test_document": "/test-document",
            "check_emails": "/cron/check-emails",
        }
    }


@app.get("/test-imap", tags=["Testing"])
async def test_imap() -> Dict[str, Any]:
    """
    Teste la connexion IMAP Gmail et affiche les informations de debug.

    Cet endpoint permet de vérifier que:
    - Les credentials IMAP sont corrects
    - La connexion au serveur Gmail fonctionne
    - Le dossier configuré est accessible
    - On peut compter les emails non lus

    Returns:
        Dict avec les informations de connexion et statistiques.

    Example:
        GET /test-imap

        Response:
        {
            "status": "success",
            "connected": true,
            "imap_server": "imap.gmail.com",
            "imap_user": "leonie@voxperience.com",
            "folder": "INBOX",
            "total_emails": 42,
            "unseen_emails": 5
        }
    """
    logger.info("Test de connexion IMAP demandé via endpoint")
    result = test_imap_connection()
    return result


@app.get("/cron/check-emails", tags=["Cron"])
async def trigger_check_emails() -> Dict[str, Any]:
    """
    Déclenche manuellement la vérification des nouveaux emails.

    Cet endpoint permet de tester la fonction de polling IMAP
    sans attendre le scheduler automatique.

    Returns:
        Dict avec les statistiques de la vérification.

    Warning:
        En production, cet endpoint devrait être protégé par
        un token d'authentification.

    Example:
        GET /cron/check-emails

        Response:
        {
            "total_emails": 3,
            "nouveaux_dossiers": 1,
            "emails_avec_pieces_jointes": 2,
            "courtiers_identifies": 3,
            "clients_identifies": 2,
            "erreurs": 0
        }
    """
    logger.info("Vérification manuelle des emails déclenchée via endpoint")
    stats = await check_new_emails()
    return stats


from pydantic import BaseModel

class TestMistralRequest(BaseModel):
    email_subject: str
    email_body: str
    courtier_email: str = "test@test.com"

@app.post("/test-mistral", tags=["Testing"])
async def test_mistral_classification(
    request: TestMistralRequest
) -> Dict[str, Any]:
    """
    Endpoint de test pour classifier un email avec Mistral AI.

    Args:
        email_subject: Sujet de l'email.
        email_body: Corps de l'email.
        courtier_email: Email du courtier (optionnel, défaut: test@test.com).

    Returns:
        Classification Mistral avec action, résumé, confiance, détails.

    Example:
        POST /test-mistral
        {
            "email_subject": "Nouveau dossier M. Dupont",
            "email_body": "Bonjour, nouveau client Jean Dupont pour un prêt immobilier.",
            "courtier_email": "test@test.com"
        }
    """
    from datetime import datetime
    from app.models.email import EmailData
    from app.services.mistral import MistralService

    logger.info(
        f"Test classification Mistral demandé",
        extra={"subject": request.email_subject}
    )

    # Créer un email factice
    email = EmailData(
        message_id="test-123",
        from_address=request.courtier_email,
        from_name="Test",
        to_addresses=["leonie@voxperience.com"],
        subject=request.email_subject,
        body_text=request.email_body,
        date=datetime.now(),
        attachments=[]
    )

    # Courtier factice
    courtier = {
        "id": "test-id",
        "email": request.courtier_email,
        "nom": "Test",
        "prenom": "Courtier",
        "dossier_drive_id": "test-drive",
        "actif": True
    }

    # Classifier avec Mistral (client n'existe pas pour un test)
    mistral = MistralService()
    classification = await mistral.classify_email(email, courtier, client_exists=False)

    return classification.model_dump()


from fastapi import UploadFile, File
from pathlib import Path as PathlibPath

@app.post("/test-document", tags=["Testing"])
async def test_document_processing(
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    """
    Endpoint de test pour le traitement de documents.

    Teste la conversion, compression et extraction de texte sur un fichier uploadé.

    Args:
        file: Fichier à traiter (image, PDF, document Office).

    Returns:
        Dict avec les résultats du traitement:
        - conversion: Chemin du PDF converti
        - compression: Chemin du PDF compressé + tailles
        - text_extraction: Texte extrait du PDF
        - hash: Hash SHA256 du fichier
        - page_count: Nombre de pages du PDF

    Example:
        curl -X POST "http://localhost:8000/test-document" \
             -H "Content-Type: multipart/form-data" \
             -F "file=@/path/to/document.jpg"
    """
    from app.services.document import DocumentProcessor
    from app.config import get_settings
    import os

    settings = get_settings()

    logger.info(
        f"Test de traitement de document demandé",
        extra={
            "filename": file.filename,
            "content_type": file.content_type
        }
    )

    try:
        # Créer le répertoire temporaire si nécessaire
        temp_dir = PathlibPath(settings.DOCUMENT_TEMP_DIR)
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Sauvegarder le fichier uploadé temporairement
        input_path = temp_dir / file.filename
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"Fichier sauvegardé: {input_path}")

        # Initialiser le service de traitement de documents
        processor = DocumentProcessor(
            temp_dir=str(temp_dir),
            max_file_size_mb=settings.MAX_FILE_SIZE_MB,
            target_pdf_size_mb=settings.TARGET_PDF_SIZE_MB
        )

        # 1. Calculer le hash du fichier original
        file_hash = processor.calculate_file_hash(str(input_path))
        original_size_mb = input_path.stat().st_size / (1024 * 1024)

        logger.info(f"Hash calculé: {file_hash[:16]}...")

        # 2. Convertir en PDF (si nécessaire)
        pdf_path = processor.convert_to_pdf(str(input_path))
        if not pdf_path:
            raise ValueError("Échec de la conversion en PDF")

        pdf_size_mb = PathlibPath(pdf_path).stat().st_size / (1024 * 1024)
        logger.info(f"PDF converti: {pdf_path} ({pdf_size_mb:.2f} MB)")

        # 3. Compter les pages
        page_count = processor.get_pdf_page_count(pdf_path)
        logger.info(f"Nombre de pages: {page_count}")

        # 4. Extraire le texte
        extracted_text = processor.extract_text_from_pdf(pdf_path)
        text_preview = extracted_text[:200] if extracted_text else ""
        logger.info(f"Texte extrait: {len(extracted_text)} caractères")

        # 5. Compresser le PDF
        compressed_path = processor.compress_pdf(pdf_path)
        compressed_size_mb = PathlibPath(compressed_path).stat().st_size / (1024 * 1024)
        compression_ratio = (1 - compressed_size_mb / pdf_size_mb) * 100 if pdf_size_mb > 0 else 0

        logger.info(
            f"PDF compressé: {compressed_path} "
            f"({compressed_size_mb:.2f} MB, réduction de {compression_ratio:.1f}%)"
        )

        # Résultats
        result = {
            "status": "success",
            "input": {
                "filename": file.filename,
                "content_type": file.content_type,
                "size_mb": round(original_size_mb, 2),
                "hash": file_hash
            },
            "conversion": {
                "pdf_path": str(pdf_path),
                "size_mb": round(pdf_size_mb, 2),
                "page_count": page_count
            },
            "compression": {
                "compressed_path": str(compressed_path),
                "original_size_mb": round(pdf_size_mb, 2),
                "compressed_size_mb": round(compressed_size_mb, 2),
                "reduction_percent": round(compression_ratio, 1),
                "under_target": compressed_size_mb <= settings.TARGET_PDF_SIZE_MB
            },
            "text_extraction": {
                "total_chars": len(extracted_text),
                "preview": text_preview
            }
        }

        # Nettoyage optionnel (peut être désactivé pour inspection)
        # os.remove(input_path)
        # if pdf_path != str(input_path):
        #     os.remove(pdf_path)
        # os.remove(compressed_path)

        logger.info(f"Traitement de document réussi pour {file.filename}")

        return result

    except Exception as e:
        logger.error(
            f"Erreur lors du traitement du document: {e}",
            exc_info=True
        )
        return {
            "status": "error",
            "error": str(e),
            "filename": file.filename
        }


# =============================================================================
# GESTIONNAIRES D'ERREURS
# =============================================================================


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Gestionnaire d'erreur 404."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "La ressource demandée n'existe pas",
            "path": str(request.url),
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Gestionnaire d'erreur 500."""
    logger.error(f"Erreur interne: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Une erreur interne est survenue",
        }
    )


# =============================================================================
# IMPORT DES ROUTES
# =============================================================================

from app.api import webhook
from app.cron.check_emails import check_new_emails, test_imap_connection

# Inclusion des routers
app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])

# À décommenter lors des prochaines sessions:
# from app.api import admin, cron, dossiers
# app.include_router(dossiers.router, prefix="/api/dossiers", tags=["Dossiers"])
# app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
# app.include_router(cron.router, prefix="/cron", tags=["Cron"])


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
