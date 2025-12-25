"""
Tâche cron de vérification des nouveaux emails.

Ce module contient la fonction de polling IMAP qui sera appelée
périodiquement pour récupérer et traiter les nouveaux emails.
"""

import asyncio
import logging
from typing import List

from app.models.email import EmailData
from app.services.email_fetcher import EmailFetcher
from app.services.email_parser import EmailParser
from app.services.router import EmailRouter

logger = logging.getLogger(__name__)



def _fetch_emails_sync() -> List[EmailData]:
    """
    Fonction helper synchrone pour récupérer les emails via IMAP.

    Exécutée dans un thread séparé pour ne pas bloquer l'event loop.

    Returns:
        Liste des emails récupérés.
    """
    with EmailFetcher() as fetcher:
        return fetcher.fetch_new_emails()


async def check_new_emails() -> dict:
    """
    Vérifie et récupère les nouveaux emails via IMAP.
    Délègue ensuite le traitement complet à l'EmailAgent.
    """
    from app.services.email_agent import EmailAgent
    
    logger.info("=" * 60)
    logger.info("Démarrage de la vérification des nouveaux emails (via EmailAgent)")
    logger.info("=" * 60)

    # Vérification du mode maintenance (Pause Prod)
    from app.utils.db import get_config
    from app.config import get_settings
    
    settings = get_settings()
    maintenance_mode = get_config("maintenance_mode")
    
    if maintenance_mode is True:
        if settings.is_production:
            logger.warning("⚠️ MODE MAINTENANCE ACTIF (PROD) : Traitement des emails en pause sur Railway.")
            return {
                "total_emails": 0,
                "processed_success": 0,
                "processed_error": 0,
                "status": "paused"
            }
        else:
             logger.info("ℹ️ MODE MAINTENANCE (PROD) est ACTIF mais ignoré en local (DEV).")

    stats = {
        "total_emails": 0,
        "processed_success": 0,
        "processed_error": 0,
    }

    try:
        # Récupération des emails dans un thread séparé (IMAP est bloquant)
        logger.info("Récupération des emails via IMAP...")
        emails = await asyncio.to_thread(_fetch_emails_sync)

        stats["total_emails"] = len(emails)

        if not emails:
            logger.info("Aucun nouvel email trouvé depuis la dernière vérification")
            return stats

        logger.info(f"Nombre d'emails récupérés: {len(emails)}")
        
        # Initialisation de l'agent
        agent = EmailAgent()

        # Traitement de chaque email via l'Agent
        for idx, email in enumerate(emails, 1):
            logger.info(f"\n--- Email {idx}/{len(emails)} ---")
            
            try:
                success = await agent.process_incoming_email(email)
                if success:
                    stats["processed_success"] += 1
                else:
                    # L'agent renvoie False si ignoré (orphelin) ou erreur
                    logger.info("Email ignoré ou non traité par l'agent.")
            
            except Exception as e:
                logger.error(f"Erreur critique traitement agent pour email {idx}: {e}", exc_info=True)
                stats["processed_error"] += 1
                continue

    except Exception as e:
        logger.error(f"Erreur globale vérification emails: {e}", exc_info=True)

    # Affichage des statistiques finales
    logger.info("\n" + "=" * 60)
    logger.info("Statistiques de la vérification:")
    logger.info(f"  - Total emails: {stats['total_emails']}")
    logger.info(f"  - Succès Agent: {stats['processed_success']}")
    logger.info(f"  - Erreurs: {stats['processed_error']}")
    logger.info("=" * 60)

    return stats


def test_imap_connection() -> dict:
    """
    Teste la connexion IMAP et affiche des informations de debug.

    Returns:
        Dict avec les informations de connexion et le statut.

    Raises:
        Exception: Si la connexion échoue.
    """
    logger.info("Test de connexion IMAP...")

    try:
        with EmailFetcher() as fetcher:
            # La connexion a réussi si on arrive ici
            logger.info("✅ Connexion IMAP réussie")

            # Récupération du nombre d'emails non lus
            label = fetcher.settings.IMAP_LABEL
            status, messages = fetcher.imap.select(label, readonly=True)

            if status == "OK":
                # Compte les emails non lus
                status, message_numbers = fetcher.imap.search(None, "UNSEEN")
                if status == "OK":
                    num_unseen = len(message_numbers[0].split()) if message_numbers[0] else 0
                else:
                    num_unseen = 0

                # Compte tous les emails
                status, all_messages = fetcher.imap.search(None, "ALL")
                if status == "OK":
                    num_total = len(all_messages[0].split()) if all_messages[0] else 0
                else:
                    num_total = 0

                return {
                    "status": "success",
                    "connected": True,
                    "imap_server": fetcher.settings.IMAP_HOST,
                    "imap_user": fetcher.settings.IMAP_EMAIL,
                    "label": label,
                    "total_emails": num_total,
                    "unseen_emails": num_unseen,
                }
            else:
                raise Exception(f"Impossible de sélectionner le label {label}")

    except Exception as e:
        logger.error(f"❌ Erreur de connexion IMAP: {e}", exc_info=True)
        return {
            "status": "error",
            "connected": False,
            "error": str(e),
        }
