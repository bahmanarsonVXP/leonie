"""
Endpoints cron pour les tâches planifiées.

Ce module fournit les endpoints appelés par des cron jobs
ou des schedulers externes (Railway Cron, etc.).

Note: Ces endpoints ne nécessitent PAS d'authentification JWT
car ils sont appelés par des systèmes externes (Railway Cron, etc.)
"""

from datetime import datetime, timedelta
from typing import Dict, List
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, status

from app.services.notification import NotificationService
from app.utils.db import (
    get_all_courtiers_actifs,
    get_clients_modified_since,
    get_pieces_dossier,
    get_type_piece,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/cron", tags=["cron"])


@router.get("/daily-report")
async def send_daily_reports() -> Dict:
    """
    Envoie un rapport quotidien à chaque courtier actif (18h).

    Résumé envoyé par email:
    - Clients modifiés aujourd'hui
    - Nombre de pièces reçues
    - Dossiers complets
    - Alertes (pièces manquantes, non conformes)

    Returns:
        Dict avec statut et nombre de courtiers notifiés

    Note:
        Cet endpoint est appelé par un cron job (Railway, etc.)
        et ne nécessite pas d'authentification JWT.
    """
    try:
        logger.info("Début génération rapports quotidiens")

        notif = NotificationService()
        courtiers = get_all_courtiers_actifs()

        if not courtiers:
            logger.info("Aucun courtier actif, pas de rapport à envoyer")
            return {
                "status": "success",
                "message": "Aucun courtier actif",
                "courtiers_notifies": 0
            }

        today = datetime.now().date()
        since_datetime = datetime.combine(today, datetime.min.time())

        courtiers_notifies = 0

        for courtier in courtiers:
            courtier_id = UUID(courtier.get('id'))

            # Récupérer clients modifiés aujourd'hui
            clients_modified = get_clients_modified_since(
                courtier_id,
                since_datetime
            )

            if not clients_modified:
                logger.debug(
                    "Aucun client modifié pour ce courtier",
                    courtier_id=str(courtier_id),
                    courtier_email=courtier.get('email')
                )
                continue

            # Générer tableau HTML avec détails
            rows_html = []
            for client in clients_modified:
                client_id = UUID(client.get('id'))
                pieces = get_pieces_dossier(client_id)

                nb_total = len(pieces)
                nb_recues = sum(1 for p in pieces if p.get('statut') == 'recue')
                nb_manquantes = sum(1 for p in pieces if p.get('statut') == 'manquante')
                nb_non_conformes = sum(
                    1 for p in pieces
                    if p.get('statut') in ['non_conforme', 'non_reconnu']
                )

                progression = round((nb_recues / nb_total) * 100, 1) if nb_total > 0 else 0

                rows_html.append(f"""
                    <tr>
                        <td>{client.get('prenom', '')} {client.get('nom', '')}</td>
                        <td style="text-align: center;">{nb_total}</td>
                        <td style="text-align: center; color: green;">{nb_recues}</td>
                        <td style="text-align: center; color: orange;">{nb_manquantes}</td>
                        <td style="text-align: center; color: red;">{nb_non_conformes}</td>
                        <td style="text-align: center;">{progression}%</td>
                    </tr>
                """)

            # Corps HTML de l'email
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    h2 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f0f0f0; font-weight: bold; }}
                    .footer {{ margin-top: 30px; color: #666; font-size: 0.9em; }}
                </style>
            </head>
            <body>
                <h2>📊 Rapport quotidien Léonie - {today.strftime('%d/%m/%Y')}</h2>
                
                <p>Bonjour {courtier.get('prenom', '')},</p>
                
                <p>{len(clients_modified)} dossier(s) ont été modifiés aujourd'hui :</p>
                
                <table>
                    <thead>
                        <tr>
                            <th>Client</th>
                            <th>Total</th>
                            <th>Reçues</th>
                            <th>Manquantes</th>
                            <th>Non conformes</th>
                            <th>Progression</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(rows_html)}
                    </tbody>
                </table>
                
                <div class="footer">
                    <p>Cordialement,<br>Léonie 🤖</p>
                    <p><em>Rapport généré automatiquement</em></p>
                </div>
            </body>
            </html>
            """

            # Envoyer email (NotificationService doit être implémenté)
            try:
                # TODO: Implémenter NotificationService.send_email complètement
                # Pour l'instant, juste logger
                notif.send_email(
                    to=courtier.get('email'),
                    subject=f"📊 Rapport quotidien Léonie - {today.strftime('%d/%m/%Y')}",
                    body_html=html_body
                )
                logger.info(
                    "Rapport quotidien généré",
                    courtier_id=str(courtier_id),
                    courtier_email=courtier.get('email'),
                    nb_clients=len(clients_modified)
                )
                courtiers_notifies += 1
            except Exception as e:
                logger.error(
                    "Erreur envoi email rapport quotidien",
                    courtier_id=str(courtier_id),
                    courtier_email=courtier.get('email'),
                    error=str(e),
                    exc_info=True
                )
                # Continuer avec les autres courtiers

        logger.info(
            "Rapports quotidiens générés",
            nb_courtiers_notifies=courtiers_notifies,
            nb_courtiers_total=len(courtiers)
        )

        return {
            "status": "success",
            "message": f"Rapports quotidiens générés pour {courtiers_notifies} courtier(s)",
            "courtiers_notifies": courtiers_notifies,
            "courtiers_total": len(courtiers),
            "date": today.isoformat()
        }

    except Exception as e:
        logger.error(
            "Erreur génération rapports quotidiens",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération des rapports quotidiens: {str(e)}"
        )
