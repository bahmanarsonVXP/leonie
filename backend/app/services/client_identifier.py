"""
Service pour identifier automatiquement les clients depuis les emails.

Ce module résout le problème des emails forwardés en analysant:
1. Header From (expéditeur direct)
2. Headers Forward (si email transféré)
3. Corps email (mentions d'emails)
4. Classification Mistral (nom client)
"""

import re
import structlog
from typing import Dict, List, Optional
from uuid import UUID

from app.models.email import EmailData
from app.utils.db import (
    get_db,
    get_client_by_email,
    find_client_by_email_list,
    find_client_by_name,
    add_secondary_email,
    create_client_record
)

logger = structlog.get_logger()


class ClientIdentifier:
    """
    Identifie les clients depuis les emails en analysant toutes les sources.
    """

    @staticmethod
    def extract_all_emails_from_message(email: EmailData) -> List[str]:
        """
        Extrait TOUS les emails d'un message.

        Sources:
        - From (expéditeur)
        - To/CC
        - Headers de forward (si disponibles)
        - Corps du message (regex extraction)

        Args:
            email: Email à analyser

        Returns:
            Liste unique d'emails trouvés (lowercase)
        """
        emails = set()

        # 1. From
        if email.from_address:
            emails.add(email.from_address.lower())

        # 2. To et CC
        for addr in email.to_addresses + email.cc_addresses:
            if addr:
                emails.add(addr.lower())

        # 3. Analyser corps pour emails (forwards, mentions)
        body = email.body_text or email.body_html or ""

        # Pattern email standard
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        found_emails = re.findall(email_pattern, body)

        for e in found_emails:
            emails.add(e.lower())

        # 4. Chercher patterns "De : email@domain.com" (forwards Gmail/Outlook)
        forward_patterns = [
            r'De\s*:\s*(?:.*?<)?([^\s<>]+@[^\s<>]+)(?:>)?',  # Gmail FR
            r'From\s*:\s*(?:.*?<)?([^\s<>]+@[^\s<>]+)(?:>)?',  # Gmail EN
            r'Expéditeur\s*:\s*(?:.*?<)?([^\s<>]+@[^\s<>]+)(?:>)?',  # Outlook FR
            r'Fra\s*:\s*(?:.*?<)?([^\s<>]+@[^\s<>]+)(?:>)?',  # Outlook NO
        ]

        for pattern in forward_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for match in matches:
                # Nettoyer l'email extrait
                clean_email = re.sub(r'[<>"\'\(\)]', '', match).strip()
                if '@' in clean_email and '.' in clean_email:
                    emails.add(clean_email.lower())

        logger.debug(
            "Emails extraits du message",
            nb_emails=len(emails),
            emails=list(emails)
        )

        return list(emails)

    @staticmethod
    def identify_client_from_email(
        email: EmailData,
        courtier: Dict
    ) -> Optional[Dict]:
        """
        Identifie un client existant depuis un email.

        Stratégie:
        1. Extraire tous les emails du message (from + forwards + corps)
        2. Exclure email du courtier et emails système
        3. Chercher chaque email dans la table clients (principal + secondaires)
        4. Si trouvé : ajouter l'email aux secondaires si nécessaire
        5. Retourner premier match trouvé

        Args:
            email: Email reçu
            courtier: Courtier identifié (dict Supabase)

        Returns:
            Client si trouvé, None sinon
        """
        # Extraire tous emails
        all_emails = ClientIdentifier.extract_all_emails_from_message(email)

        # Exclure emails courtier et système
        excluded_emails = [
            courtier.get("email", "").lower(),
            "leonie@voxperience.com",
            "contact@voxperience.com",
            "noreply@voxperience.com"
        ]

        candidate_emails = [
            e for e in all_emails
            if e not in excluded_emails and e
        ]

        logger.info(
            "Recherche client par emails",
            candidate_emails=candidate_emails,
            courtier_id=courtier.get("id")
        )

        # Chercher dans DB via find_client_by_email_list
        courtier_uuid = UUID(courtier.get("id"))
        client = find_client_by_email_list(candidate_emails, courtier_uuid)

        if client:
            matched_email = None

            # Identifier quel email a matché
            client_email_principal = client.get("email_principal", "").lower()
            if client_email_principal in candidate_emails:
                matched_email = client_email_principal

            if not matched_email:
                emails_secondaires = [e.lower() for e in (client.get("emails_secondaires") or [])]
                for email_candidate in candidate_emails:
                    if email_candidate in emails_secondaires:
                        matched_email = email_candidate
                        break

            logger.info(
                "Client identifié par email",
                client_id=client.get("id"),
                matched_email=matched_email,
                client_nom=f"{client.get('prenom')} {client.get('nom')}"
            )

            # Si email trouvé n'est pas le principal ni dans secondaires, l'ajouter
            if matched_email and matched_email != client_email_principal:
                client_emails_secondaires = [e.lower() for e in (client.get("emails_secondaires") or [])]
                if matched_email not in client_emails_secondaires:
                    add_secondary_email(UUID(client.get("id")), matched_email)

            return client

        # Pas trouvé
        logger.info("Aucun client trouvé pour ces emails")
        return None

    @staticmethod
    def create_client_from_email_and_classification(
        email: EmailData,
        courtier: Dict,
        classification: Dict,
        drive_manager
    ) -> Dict:
        """
        Crée un nouveau client depuis un email + classification Mistral.

        Étapes:
        1. Extraire nom/prénom depuis classification
        2. Extraire email client (premier non-courtier)
        3. Créer dossier Drive
        4. Créer client en DB

        Args:
            email: Email reçu
            courtier: Courtier (dict Supabase)
            classification: Classification Mistral (dict)
            drive_manager: Instance DriveManager

        Returns:
            Client créé (dict Supabase)

        Raises:
            ValueError: Si nom client manquant dans classification
        """
        details = classification.get('details', {})

        # 1. Infos client depuis classification
        client_nom = details.get('client_nom')
        client_prenom = details.get('client_prenom')
        type_pret = details.get('type_pret', 'immobilier')

        if not client_nom:
            raise ValueError("Impossible de créer client : nom manquant dans classification")

        # 2. Email client
        all_emails = ClientIdentifier.extract_all_emails_from_message(email)
        excluded_emails = [
            courtier.get("email", "").lower(),
            "leonie@voxperience.com",
            "contact@voxperience.com",
            "noreply@voxperience.com"
        ]
        candidate_emails = [e for e in all_emails if e not in excluded_emails and e]

        # Utiliser premier email trouvé, sinon générer temporaire
        if candidate_emails:
            client_email = candidate_emails[0]
            logger.info(f"Email client identifié: {client_email}")
        else:
            # Email temporaire (sera mis à jour ultérieurement)
            client_email = f"{client_prenom or 'client'}.{client_nom}@temp.leonie.local".lower()
            logger.warning(
                "Aucun email client trouvé, email temporaire créé",
                temp_email=client_email
            )

        # 3. Créer dossier Drive
        from app.services.drive import DriveManager

        # Utiliser le dossier du courtier comme parent
        courtier_folder_id = courtier.get('dossier_drive_id')

        if not courtier_folder_id:
            raise ValueError(
                f"Courtier {courtier.get('id')} n'a pas de dossier_drive_id. "
                "Impossible de créer dossier client."
            )

        # Créer dossier client
        client_folder_name = f"CLIENT_{client_nom}_{client_prenom or ''}".strip()
        client_folder_id = drive_manager.get_or_create_folder(
            client_folder_name,
            courtier_folder_id
        )

        logger.info(
            "Dossier Drive créé pour nouveau client",
            folder_name=client_folder_name,
            folder_id=client_folder_id
        )

        # 4. Créer client en DB
        client_data = {
            'courtier_id': courtier.get('id'),
            'nom': client_nom,
            'prenom': client_prenom or '',
            'email_principal': client_email,
            'type_pret': type_pret,
            'statut': 'en_cours',
            'dossier_drive_id': client_folder_id
        }

        client = create_client_record(client_data)

        logger.info(
            "Client créé automatiquement",
            client_id=client.get('id'),
            client_nom=f"{client_prenom} {client_nom}",
            email=client_email,
            type_pret=type_pret
        )

        return client
