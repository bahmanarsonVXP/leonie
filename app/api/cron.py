"""
Endpoints cron pour les tâches planifiées.

Ce module fournit les endpoints appelés par des cron jobs
ou des schedulers externes (Railway Cron, etc.).

TODO (Session 5): Implémenter les endpoints cron
"""

from fastapi import APIRouter

router = APIRouter()


# TODO: Implémenter GET /cron/daily-report
# @router.get("/daily-report")
# async def send_daily_reports():
#     """Envoie les rapports quotidiens aux courtiers."""
#     pass


# TODO: Implémenter GET /cron/poll-emails
# @router.get("/poll-emails")
# async def poll_imap_emails():
#     """Polling IMAP pour récupérer les nouveaux emails."""
#     pass
