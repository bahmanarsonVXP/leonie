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

    Cette fonction:
    1. Se connecte au serveur IMAP Gmail
    2. Récupère les emails depuis la dernière vérification (SINCE timestamp)
    3. Pour chaque email:
       a. Identifie le courtier expéditeur
       b. Identifie le client (si existe)
       c. Log les informations
    4. Met à jour le timestamp de dernière vérification

    Returns:
        Dict avec les statistiques de la vérification.

    Note:
        La classification Mistral et le routing vers workflows seront
        implémentés dans la Session 3+.

        Pour l'instant, cette fonction récupère et log les emails.

    Usage:
        Cette fonction est destinée à être appelée périodiquement
        par un scheduler (APScheduler, Celery, ou cron système).
    """
    logger.info("=" * 60)
    logger.info("Démarrage de la vérification des nouveaux emails")
    logger.info("=" * 60)

    stats = {
        "total_emails": 0,
        "courtiers_identifies": 0,
        "clients_identifies": 0,
        "emails_avec_pieces_jointes": 0,
        "erreurs": 0,
    }

    try:
        # Récupération des emails dans un thread séparé (IMAP est bloquant)
        logger.info("Récupération des emails via IMAP (opération bloquante dans thread séparé)...")
        emails = await asyncio.to_thread(_fetch_emails_sync)

        stats["total_emails"] = len(emails)

        if not emails:
            logger.info("Aucun nouvel email trouvé depuis la dernière vérification")
            return stats

        logger.info(f"Nombre d'emails récupérés: {len(emails)}")

        # Traitement de chaque email
        for idx, email in enumerate(emails, 1):
            logger.info(f"\n--- Email {idx}/{len(emails)} ---")

            try:
                # Affichage du résumé de l'email
                summary = EmailParser.get_email_summary(email)
                logger.info(f"Résumé:\n{summary}")

                # Vérification présence pièces jointes
                if EmailParser.has_attachments(email):
                    stats["emails_avec_pieces_jointes"] += 1
                    logger.info(f"📎 {len(email.attachments)} pièce(s) jointe(s) détectée(s):")
                    for att_idx, attachment in enumerate(email.attachments, 1):
                        logger.info(
                            f"  [{att_idx}] {attachment.filename} "
                            f"({attachment.content_type}, {attachment.size_bytes} octets)"
                        )

                # Identification du courtier
                courtier = EmailParser.identify_courtier(email)
                if courtier:
                    stats["courtiers_identifies"] += 1
                    logger.info(
                        f"✅ Courtier identifié: {courtier.get('prenom')} "
                        f"{courtier.get('nom')} ({courtier.get('email')})"
                    )

                    # Identification du client (seulement si courtier trouvé)
                    client = EmailParser.identify_client(email, courtier.get("id"))
                    if client:
                        stats["clients_identifies"] += 1
                        logger.info(
                            f"✅ Client identifié: {client.get('prenom')} "
                            f"{client.get('nom')} ({client.get('email_principal')})"
                        )
                    else:
                        logger.info("ℹ️  Client non identifié (nouveau dossier ou client inconnu)")

                        # Extraction infos client pour création future
                        client_info = EmailParser.extract_client_info_from_email(email)
                        logger.info(
                            f"ℹ️  Informations client extraites: {client_info}"
                        )

                    # Classification Mistral (passe le client pour contexte)
                    classification = await EmailParser.classify_with_mistral(email, courtier, client)
                    logger.info(
                        f"📊 Classification Mistral: {classification.action.value} "
                        f"(confiance: {classification.confiance})"
                    )
                    logger.info(f"📝 Résumé: {classification.resume}")
                    logger.info(f"📋 Détails: {classification.details}")

                    # Routing vers workflow approprié (Session 6)
                    result = await EmailRouter.route(email, classification, courtier)
                    logger.info(f"✅ Traitement: {result}")

                else:
                    logger.warning(
                        f"⚠️  Courtier non identifié pour l'email: {email.from_address}"
                    )
                    logger.info(
                        "Email ignoré (expéditeur non autorisé). "
                        "Créez un courtier dans Supabase si nécessaire."
                    )

            except Exception as e:
                logger.error(
                    f"Erreur lors du traitement de l'email {idx}: {e}",
                    exc_info=True
                )
                stats["erreurs"] += 1
                continue

    except Exception as e:
        logger.error(
            f"Erreur lors de la vérification des emails: {e}",
            exc_info=True
        )
        stats["erreurs"] += 1

    # Affichage des statistiques finales
    logger.info("\n" + "=" * 60)
    logger.info("Statistiques de la vérification:")
    logger.info(f"  - Total emails récupérés: {stats['total_emails']}")
    logger.info(f"  - Courtiers identifiés: {stats['courtiers_identifies']}")
    logger.info(f"  - Clients identifiés: {stats['clients_identifies']}")
    logger.info(f"  - Emails avec pièces jointes: {stats['emails_avec_pieces_jointes']}")
    logger.info(f"  - Erreurs: {stats['erreurs']}")
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
