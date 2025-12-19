"""
Service de parsing des emails.

Ce module extrait les informations utiles des emails reçus
et identifie les courtiers et clients associés.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from app.models.client import Client
from app.models.courtier import Courtier
from app.models.email import EmailAction, EmailClassification, EmailData
from app.utils.db import (
    find_client_by_email_list,
    get_client_by_email,
    get_courtier_by_email,
)

logger = logging.getLogger(__name__)


class EmailParser:
    """
    Service de parsing et d'analyse des emails.

    Fournit des méthodes statiques pour identifier les courtiers,
    clients et classifier les emails avec Mistral AI.
    """

    @staticmethod
    def parse(raw_email_data: dict) -> EmailData:
        """
        Transforme un dict brut en modèle Pydantic EmailData.

        Args:
            raw_email_data: Dict contenant les données de l'email.

        Returns:
            EmailData validé par Pydantic.

        Note:
            Cette méthode est utile si vous recevez des données brutes
            d'un webhook ou autre source. EmailFetcher retourne déjà
            des objets EmailData validés.
        """
        try:
            return EmailData(**raw_email_data)
        except Exception as e:
            logger.error(f"Erreur lors du parsing de l'email: {e}")
            raise

    @staticmethod
    async def classify_with_mistral(
        email: EmailData,
        courtier: Dict,
        client: Optional[Dict] = None
    ) -> EmailClassification:
        """
        Utilise Mistral AI pour classifier l'email et extraire les informations.

        Cette méthode analyse le contenu de l'email (sujet, corps, pièces jointes)
        pour déterminer l'action appropriée et extraire les informations pertinentes.

        Args:
            email: Email à classifier.
            courtier: Courtier identifié (dict Supabase).
            client: Client identifié (dict Supabase) ou None si nouveau client.

        Returns:
            EmailClassification avec action + détails.

        Example:
            >>> classification = await EmailParser.classify_with_mistral(email, courtier, client)
            >>> if classification.action == EmailAction.NOUVEAU_DOSSIER:
            ...     # Créer nouveau dossier
            ...     pass
        """
        from app.services.mistral import MistralService

        client_exists = client is not None

        logger.info(
            "Classification de l'email avec Mistral AI",
            extra={
                "email_subject": email.subject,
                "courtier_email": courtier.get("email"),
                "client_exists": client_exists
            }
        )

        # Initialiser le service Mistral
        mistral = MistralService()

        # Classifier l'email avec information sur l'existence du client
        classification = await mistral.classify_email(email, courtier, client_exists=client_exists)

        return classification

    @staticmethod
    def has_attachments(email: EmailData) -> bool:
        """
        Vérifie si l'email contient des pièces jointes.

        Args:
            email: Email à vérifier.

        Returns:
            bool: True si l'email a des pièces jointes.
        """
        has_att = len(email.attachments) > 0
        logger.debug(
            f"Email {email.message_id}: "
            f"{len(email.attachments)} pièce(s) jointe(s)"
        )
        return has_att

    @staticmethod
    def identify_courtier(email: EmailData) -> Optional[Dict]:
        """
        Identifie le courtier à partir de l'adresse de l'expéditeur.

        Args:
            email: Email à analyser.

        Returns:
            Dict contenant les données du courtier ou None si non trouvé.
        """
        sender_email = email.from_address

        logger.info(f"Recherche du courtier avec email: {sender_email}")

        try:
            courtier = get_courtier_by_email(sender_email)

            if courtier:
                logger.info(
                    f"Courtier identifié: {courtier.get('prenom')} "
                    f"{courtier.get('nom')} (ID: {courtier.get('id')})"
                )
                return courtier
            else:
                logger.warning(
                    f"Aucun courtier trouvé pour l'email: {sender_email}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Erreur lors de l'identification du courtier: {e}",
                exc_info=True
            )
            return None

    @staticmethod
    def identify_client(
        email: EmailData,
        courtier_id: str
    ) -> Optional[Dict]:
        """
        Identifie le client à partir de l'email expéditeur.

        Recherche le client par:
        1. Email expéditeur dans email_principal
        2. Email expéditeur dans emails_secondaires
        3. Emails en CC/TO (peut contenir co-emprunteur)

        Args:
            email: Email à analyser.
            courtier_id: ID du courtier pour filtrer la recherche.

        Returns:
            Dict contenant les données du client ou None si non trouvé.
        """
        logger.info(
            f"Recherche du client pour le courtier {courtier_id}"
        )

        try:
            courtier_uuid = UUID(courtier_id)

            # Recherche par email expéditeur d'abord
            sender_email = email.from_address
            client = get_client_by_email(sender_email, courtier_uuid)

            if client:
                logger.info(
                    f"Client identifié par email expéditeur: "
                    f"{client.get('prenom')} {client.get('nom')} "
                    f"(ID: {client.get('id')})"
                )
                return client

            # Si pas trouvé, recherche dans tous les emails (TO, CC)
            # pour gérer le cas des co-emprunteurs
            all_emails = [sender_email] + email.to_addresses + email.cc_addresses

            # Retire les adresses systèmes de la recherche
            # (peut être étendu avec d'autres adresses systèmes si besoin)
            system_emails = [
                "leonie@voxperience.com",
                "contact@voxperience.com",
                "noreply@voxperience.com"
            ]
            all_emails = [
                e for e in all_emails
                if e.lower() not in [s.lower() for s in system_emails]
            ]

            logger.debug(
                f"Recherche du client dans la liste d'emails: {all_emails}"
            )

            client = find_client_by_email_list(all_emails, courtier_uuid)

            if client:
                logger.info(
                    f"Client identifié par emails multiples: "
                    f"{client.get('prenom')} {client.get('nom')} "
                    f"(ID: {client.get('id')})"
                )
                return client
            else:
                logger.warning(
                    f"Aucun client trouvé pour les emails: {all_emails}"
                )
                return None

        except ValueError as e:
            logger.error(f"ID courtier invalide: {courtier_id}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Erreur lors de l'identification du client: {e}",
                exc_info=True
            )
            return None

    @staticmethod
    def extract_client_info_from_email(email: EmailData) -> Dict[str, any]:
        """
        Extrait les informations potentielles d'un nouveau client depuis l'email.

        Utile pour pré-remplir un formulaire de création de client.

        Args:
            email: Email à analyser.

        Returns:
            Dict avec les informations extraites (nom, prénom, emails).
        """
        # Extraction du nom et prénom depuis from_name
        nom = None
        prenom = None

        if email.from_name:
            # Essaie de séparer prénom nom (format: "Prénom Nom")
            parts = email.from_name.strip().split()
            if len(parts) >= 2:
                prenom = parts[0]
                nom = " ".join(parts[1:])
            elif len(parts) == 1:
                nom = parts[0]

        # Extraction des emails
        email_principal = email.from_address

        # Emails secondaires: TO et CC sans adresses systèmes
        system_emails = [
            "leonie@voxperience.com",
            "contact@voxperience.com",
            "noreply@voxperience.com"
        ]

        emails_secondaires = list(set(
            email.to_addresses + email.cc_addresses
        ))
        emails_secondaires = [
            e for e in emails_secondaires
            if e.lower() not in [s.lower() for s in system_emails]
            and e != email_principal
        ]

        info = {
            "nom": nom,
            "prenom": prenom,
            "email_principal": email_principal,
            "emails_secondaires": emails_secondaires,
        }

        logger.debug(f"Informations client extraites: {info}")
        return info

    @staticmethod
    def get_email_summary(email: EmailData) -> str:
        """
        Génère un résumé textuel de l'email pour les logs.

        Args:
            email: Email à résumer.

        Returns:
            String résumé de l'email.
        """
        summary = (
            f"De: {email.from_name or 'Inconnu'} <{email.from_address}>\n"
            f"À: {', '.join(email.to_addresses)}\n"
        )

        if email.cc_addresses:
            summary += f"CC: {', '.join(email.cc_addresses)}\n"

        summary += (
            f"Sujet: {email.subject}\n"
            f"Date: {email.date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Pièces jointes: {len(email.attachments)}\n"
        )

        if email.attachments:
            summary += "Fichiers:\n"
            for att in email.attachments:
                summary += f"  - {att.filename} ({att.size_bytes} bytes)\n"

        return summary
