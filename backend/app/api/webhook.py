"""
Endpoint webhook pour le traitement des emails.

Ce module gère la réception et le traitement des emails
via webhook ou polling IMAP.
"""

import logging
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/email")
async def process_email_webhook(
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, str]:
    """
    Endpoint webhook pour traiter les emails entrants.

    Pour l'instant, cet endpoint est basique et sert principalement
    pour les tests. La vraie logique de traitement sera implémentée
    dans les prochaines sessions.

    Args:
        request: Requête FastAPI contenant le payload.
        background_tasks: Tasks en background pour traitement asynchrone.

    Returns:
        Dict avec le statut de la requête.

    Note:
        Dans une implémentation complète, cet endpoint:
        1. Validerait le payload (signature, token, etc.)
        2. Extrairait les données de l'email
        3. Appellerait EmailParser pour identifier courtier/client
        4. Déclencherait le traitement des pièces jointes
        5. Stockerait les résultats en base de données
    """
    logger.info("Webhook email reçu")

    try:
        # Récupération du payload (vide pour l'instant)
        # Dans une vraie implémentation, on attendrait un JSON avec les données de l'email
        # body = await request.json()
        # logger.debug(f"Payload webhook: {body}")

        # Pour l'instant, on log juste la réception
        logger.info("Webhook traité avec succès (mode test)")

        return {
            "status": "ok",
            "message": "Webhook email reçu et traité"
        }

    except Exception as e:
        logger.error(f"Erreur lors du traitement du webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du traitement du webhook: {str(e)}"
        )


@router.get("/email/test")
async def test_webhook_endpoint() -> Dict[str, str]:
    """
    Endpoint de test pour vérifier que le webhook fonctionne.

    Returns:
        Dict avec un message de confirmation.
    """
    return {
        "status": "ok",
        "message": "Webhook endpoint is working",
        "endpoint": "POST /webhook/email"
    }
