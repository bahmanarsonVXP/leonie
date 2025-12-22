"""
Service d'envoi de notifications par email.

Ce module gère l'envoi d'emails de notification aux courtiers
via SMTP.

TODO (Session 5): Implémenter l'envoi de notifications
"""

from typing import List, Optional


class NotificationService:
    """Service d'envoi de notifications par email."""

    def __init__(self):
        """Initialise le service de notification."""
        # TODO: Initialiser la connexion SMTP
        pass

    def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Envoie un email.

        Args:
            to: Adresse email du destinataire.
            subject: Sujet de l'email.
            body_html: Corps de l'email en HTML.
            body_text: Corps de l'email en texte brut (optionnel).
            attachments: Liste de chemins de fichiers à joindre (optionnel).

        Returns:
            bool: True si envoi réussi.

        TODO: Implémenter l'envoi d'email
        """
        pass

    def send_daily_report(self, courtier_email: str, report_path: str) -> bool:
        """
        Envoie le rapport quotidien à un courtier.

        Args:
            courtier_email: Email du courtier.
            report_path: Chemin du fichier de rapport.

        Returns:
            bool: True si envoi réussi.

        TODO: Implémenter l'envoi du rapport quotidien
        """
        pass
