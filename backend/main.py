"""
Léonie - Agent IA pour courtiers en prêts immobiliers et professionnels.

Point d'entrée de l'application FastAPI.

Déployé sur Railway avec structure monorepo (backend/ + frontend/).
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
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

    # Initialisation du Scheduler pour les tâches de fond
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from app.cron.check_emails import check_new_emails
    from app.utils.db import get_config

    scheduler = AsyncIOScheduler()
    
    # Récupérer l'intervalle de polling depuis la config (défaut: 120 secondes)
    try:
        polling_interval = get_config("email_polling_interval")
        
        interval_seconds = 120 # Défaut
        
        if polling_interval:
            # Si c'est un dict ({"minutes": 2}), on extrait la valeur
            if isinstance(polling_interval, dict):
                if "seconds" in polling_interval:
                    interval_seconds = int(polling_interval["seconds"])
                elif "minutes" in polling_interval:
                    interval_seconds = int(polling_interval["minutes"]) * 60
            else:
                # Si c'est une valeur directe (str ou int), on suppose des SECONDES
                # comme indiqué dans la description de la config ("300" = 5 min)
                interval_seconds = int(polling_interval)
            
        # Minimum 60 secondes pour éviter le spam
        interval_seconds = max(60, interval_seconds)
        logger.info(f"Intervalle de polling configuré: {interval_seconds} secondes")
        
    except Exception as e:
        logger.warning(f"Erreur lecture config polling, utilisation défaut 120s: {e}")
        interval_seconds = 120

    # Tâche 1: Vérification des emails
    scheduler.add_job(
        check_new_emails, 
        'interval', 
        seconds=interval_seconds, 
        id='check_emails_job',
        replace_existing=True
    )
    logger.info(f"Tâche planifiée: check_emails (toutes les {interval_seconds} secondes)")

    scheduler.start()
    logger.info("Scheduler démarré")

    yield

    # Shutdown
    logger.info("Arrêt de l'application...")
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler arrêté")


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
    
    # Vérifier les dépendances système
    import subprocess
    import shutil
    
    def check_command(cmd_name: str, version_args: list, possible_paths: list = None) -> tuple[str, str]:
        """Vérifie si une commande est disponible et retourne son statut et version."""
        try:
            cmd = None
            if possible_paths:
                for path in possible_paths:
                    if shutil.which(path) or Path(path).exists():
                        cmd = path
                        break
            else:
                cmd = shutil.which(cmd_name)
            
            if cmd:
                result = subprocess.run(
                    [cmd] + version_args,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip() or result.stderr.strip() or "installed"
                    return "ok", version
                else:
                    return "error", None
            else:
                return "not_found", None
        except Exception as e:
            return f"error: {str(e)}", None
    
    # Vérifier LibreOffice
    libreoffice_status, libreoffice_version = check_command(
        "libreoffice",
        ["--version"],
        ["libreoffice", "/usr/bin/libreoffice", "soffice"]
    )
    
    # Vérifier Ghostscript
    ghostscript_status, ghostscript_version = check_command(
        "gs",
        ["--version"],
        ["gs", "/usr/bin/gs"]
    )
    
    # Vérifier Poppler (pdfinfo)
    poppler_status, poppler_version = check_command(
        "pdfinfo",
        ["-v"],
        ["pdfinfo", "/usr/bin/pdfinfo"]
    )

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {
            "database": "ok",  # TODO: Vérifier Supabase
            "redis": "ok",     # TODO: Vérifier Redis
            "libreoffice": libreoffice_status,
            "libreoffice_version": libreoffice_version,
            "ghostscript": ghostscript_status,
            "ghostscript_version": ghostscript_version,
            "poppler": poppler_status,
            "poppler_version": poppler_version,
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
            "test_drive": "/test-drive",
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


@app.post("/test-drive", tags=["Testing"])
async def test_drive_operations() -> Dict[str, Any]:
    """
    Endpoint de test pour Google Drive.

    Teste la création de dossiers et l'upload de fichiers sur Drive.

    Returns:
        Dict avec les résultats des opérations Drive:
        - connection: Status de connexion
        - folder_creation: Test création dossier
        - file_upload: Test upload fichier
        - shareable_link: Lien de partage généré

    Example:
        curl -X POST "http://localhost:8000/test-drive"

    Note:
        Nécessite GOOGLE_CREDENTIALS_JSON et GOOGLE_DRIVE_MASTER_FOLDER_ID
        configurés dans les variables d'environnement.
    """
    try:
        from app.services.drive import DriveManager
        from app.services.document import DocumentProcessor
        from pathlib import Path
        import tempfile

        logger.info("Test Google Drive demandé")

        result = {
            "status": "success",
            "connection": {},
            "folder_creation": {},
            "file_upload": {},
            "shareable_link": None
        }

        # 1. Tester la connexion
        try:
            drive_manager = DriveManager()
            result["connection"] = {
                "status": "ok",
                "master_folder_id": drive_manager.master_folder_id
            }
            logger.info("✅ Connexion Google Drive réussie")
        except Exception as e:
            result["status"] = "error"
            result["connection"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"❌ Erreur connexion Drive: {e}")
            return result

        # 2. Tester la création de dossier
        try:
            # Créer un dossier de test
            test_folder_name = "TEST_Leonie_Drive"

            # Vérifier si existe déjà
            existing_folder_id = drive_manager.folder_exists(
                test_folder_name,
                drive_manager.master_folder_id
            )

            if existing_folder_id:
                folder_id = existing_folder_id
                result["folder_creation"] = {
                    "status": "existing",
                    "folder_id": folder_id,
                    "folder_name": test_folder_name
                }
                logger.info(f"✅ Dossier test existant: {folder_id}")
            else:
                folder_id = drive_manager.create_folder(
                    test_folder_name,
                    drive_manager.master_folder_id
                )
                result["folder_creation"] = {
                    "status": "created",
                    "folder_id": folder_id,
                    "folder_name": test_folder_name
                }
                logger.info(f"✅ Dossier test créé: {folder_id}")

        except Exception as e:
            result["folder_creation"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"❌ Erreur création dossier: {e}")

        # 3. Tester l'upload d'un fichier
        try:
            # Créer un PDF de test
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False
            ) as temp_file:
                temp_file.write("Test fichier Léonie pour Google Drive\n")
                temp_file.write(f"Généré le: {datetime.utcnow().isoformat()}\n")
                temp_txt_path = Path(temp_file.name)

            # Convertir en PDF
            processor = DocumentProcessor()

            # Pour le test, créer un simple fichier texte et le considérer comme PDF
            # (ou utiliser une vraie image si disponible)
            test_pdf_path = Path(tempfile.gettempdir()) / "test_leonie_drive.pdf"

            # Si on a une image de test, l'utiliser
            test_image = Path("/tmp/test_image.jpg")
            if test_image.exists():
                pdf_path = processor.convert_to_pdf(str(test_image))
            else:
                # Créer un PDF simple avec Pillow
                from PIL import Image
                img = Image.new('RGB', (400, 200), color=(73, 109, 137))
                img.save(test_pdf_path, 'PDF')
                pdf_path = str(test_pdf_path)

            # Upload sur Drive
            file_id = drive_manager.upload_file(
                Path(pdf_path),
                folder_id,
                filename="test_leonie_upload.pdf"
            )

            result["file_upload"] = {
                "status": "uploaded",
                "file_id": file_id,
                "filename": "test_leonie_upload.pdf",
                "folder_id": folder_id
            }
            logger.info(f"✅ Fichier uploadé: {file_id}")

            # 4. Générer un lien partageable
            try:
                shareable_link = drive_manager.get_shareable_link(file_id)
                result["shareable_link"] = shareable_link
                logger.info(f"✅ Lien partageable: {shareable_link}")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de générer lien partageable: {e}")

            # Nettoyage fichiers temporaires
            try:
                if temp_txt_path.exists():
                    temp_txt_path.unlink()
                if test_pdf_path.exists():
                    test_pdf_path.unlink()
            except:
                pass

        except Exception as e:
            result["file_upload"] = {
                "status": "error",
                "error": str(e)
            }
            logger.error(f"❌ Erreur upload fichier: {e}", exc_info=True)

        logger.info(f"Test Google Drive terminé: {result['status']}")
        return result

    except Exception as e:
        logger.error(
            f"Erreur lors du test Google Drive: {e}",
            exc_info=True
        )
        return {
            "status": "error",
            "error": str(e),
            "message": "Erreur lors du test Google Drive. Vérifiez les variables d'environnement."
        }


@app.get("/debug/test-smtp", tags=["Testing"])
async def test_smtp_connectivity() -> Dict[str, Any]:
    """
    Endpoint de test pour l'envoi d'email (Via Resend).
    Envoie un email de test à arsonbahman@gmail.com.
    """
    from app.services.smtp import SmtpService
    
    logger.info("TEST Email (Resend) demandé via endpoint /debug/test-smtp")
    
    try:
        smtp = SmtpService()
        success = smtp.send_email(
            to_email="arsonbahman@gmail.com",
            subject="[TEST RAILWAY] Test de connectivité Resend (Verified Domain)",
            html_content="<p>Ceci est un email de test envoyé via <strong>Resend API</strong> avec le domaine vérifié <em>voxperience.com</em>.</p>"
        )
        
        return {
            "status": "success" if success else "error", 
            "sent": success,
            "provider": "resend",
            "message": "Email de test envoyé à arsonbahman@gmail.com (Domaine vérifié)" if success else "Échec envoi Resend"
        }
    except Exception as e:
        logger.error(f"Erreur test Resend: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "provider": "resend"
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

# Routes API
from app.api import admin, cron, dossiers

app.include_router(dossiers.router, tags=["dossiers"])
app.include_router(admin.router, tags=["admin"])
app.include_router(cron.router, tags=["cron"])


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
