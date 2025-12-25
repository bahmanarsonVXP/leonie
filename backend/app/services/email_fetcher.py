"""
Service de récupération des emails via IMAP.

Ce module gère la connexion IMAP Gmail et la récupération
des emails avec leurs pièces jointes.
"""

import base64
import email
import imaplib
import logging
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from email.message import Message
from typing import List, Optional

from app.config import get_settings
from app.models.email import EmailAttachment, EmailData
from app.utils.db import get_config, set_config

logger = logging.getLogger(__name__)


class EmailFetcher:
    """
    Service de récupération des emails via IMAP.

    Gère la connexion à Gmail via IMAP, la récupération des emails
    non lus, le parsing des messages et pièces jointes.
    """

    def __init__(self):
        """Initialise le fetcher IMAP avec les settings de l'application."""
        self.settings = get_settings()
        self.imap: Optional[imaplib.IMAP4_SSL] = None
        self.connected = False

    def connect(self) -> bool:
        """
        Connecte au serveur IMAP Gmail avec retry.

        Returns:
            bool: True si connexion réussie.

        Raises:
            Exception: Si la connexion échoue après 3 tentatives.
        """
        max_retries = 3

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    f"Tentative de connexion IMAP {attempt}/{max_retries} "
                    f"à {self.settings.IMAP_HOST}:{self.settings.IMAP_PORT}"
                )

                # Connexion SSL au serveur IMAP
                self.imap = imaplib.IMAP4_SSL(
                    self.settings.IMAP_HOST,
                    self.settings.IMAP_PORT
                )

                # Authentification
                self.imap.login(
                    self.settings.IMAP_EMAIL,
                    self.settings.IMAP_PASSWORD
                )

                self.connected = True
                logger.info(
                    f"Connexion IMAP réussie pour {self.settings.IMAP_EMAIL}"
                )
                return True

            except imaplib.IMAP4.error as e:
                error_msg = str(e)
                logger.error(
                    f"Erreur d'authentification IMAP (tentative {attempt}/{max_retries}): {error_msg}"
                )
                logger.error(
                    f"Email utilisé: {self.settings.IMAP_EMAIL}, "
                    f"Host: {self.settings.IMAP_HOST}:{self.settings.IMAP_PORT}"
                )
                
                if attempt == max_retries:
                    # Message d'aide plus détaillé
                    detailed_error = (
                        f"Échec d'authentification IMAP après {max_retries} tentatives. "
                        f"Erreur: {error_msg}. "
                        f"Vérifiez que vous utilisez un App Password Gmail (pas le mot de passe principal) "
                        f"et que l'authentification à 2 facteurs est activée."
                    )
                    raise Exception(detailed_error) from e

            except Exception as e:
                logger.error(
                    f"Erreur de connexion IMAP (tentative {attempt}): {e}"
                )
                if attempt == max_retries:
                    raise Exception(
                        f"Échec de connexion IMAP après {max_retries} tentatives"
                    ) from e

        return False

    def fetch_new_emails(self) -> List[EmailData]:
        """
        Récupère les nouveaux emails (UNSEEN) depuis la dernière vérification.

        Utilise un timestamp sauvegardé dans Supabase config pour éviter
        de retraiter les mêmes emails, ET filtre sur UNSEEN pour éviter les boucles.

        Returns:
            Liste des emails récupérés et parsés.

        Raises:
            Exception: Si la connexion n'est pas établie.
        """
        if not self.connected or not self.imap:
            raise Exception("Connexion IMAP non établie. Appelez connect() d'abord.")

        try:
            # Sélection du label Gmail
            label = self.settings.IMAP_LABEL
            logger.info(f"Sélection du label Gmail: {label}")

            status, messages = self.imap.select(label)
            if status != "OK":
                logger.error(f"Impossible de sélectionner le label {label}")
                return []

            # Récupération du timestamp de la dernière vérification
            last_check_config = get_config("last_email_check")

            if last_check_config and "timestamp" in last_check_config:
                # Timestamp existant : récupérer depuis cette date
                last_timestamp = datetime.fromisoformat(last_check_config["timestamp"])
                logger.info(f"Dernière vérification: {last_timestamp.isoformat()}")
            else:
                # Première exécution : récupérer les 7 derniers jours
                last_timestamp = datetime.now(timezone.utc) - timedelta(days=7)
                logger.info(
                    f"Première exécution détectée. "
                    f"Récupération des emails depuis: {last_timestamp.isoformat()}"
                )
                # Créer la config
                set_config(
                    "last_email_check",
                    {"timestamp": last_timestamp.isoformat()},
                    "Dernière vérification emails IMAP"
                )

            # Formater la date pour IMAP (format: DD-Mon-YYYY, ex: 15-Jan-2024)
            date_str = last_timestamp.strftime("%d-%b-%Y")
            
            # CRITICAL FIX: Utiliser UNSEEN + SINCE pour éviter les boucles infinies
            logger.info(f"Recherche des emails UNSEEN SINCE: {date_str}")
            status, message_numbers = self.imap.search(None, f'(UNSEEN SINCE "{date_str}")')
            
            if status != "OK":
                logger.error("Erreur lors de la recherche des emails")
                return []

            email_ids = message_numbers[0].split()
            logger.info(f"Nombre d'emails trouvés (UNSEEN) depuis {date_str}: {len(email_ids)}")

            # Récupération et parsing des emails
            emails = []
            for email_id in email_ids:
                try:
                    email_data = self._fetch_and_parse_email(email_id)
                    if email_data:
                        emails.append(email_data)
                        logger.info(
                            f"Email parsé: {email_data.subject} "
                            f"de {email_data.from_address}"
                        )
                except Exception as e:
                    logger.error(
                        f"Erreur lors du parsing de l'email {email_id}: {e}",
                        exc_info=True
                    )
                    continue

            logger.info(f"Total d'emails récupérés avec succès: {len(emails)}")

            # Mise à jour du timestamp après récupération réussie
            now = datetime.now(timezone.utc)
            set_config(
                "last_email_check",
                {"timestamp": now.isoformat()},
                "Dernière vérification emails IMAP"
            )
            logger.info(f"Timestamp mis à jour: {now.isoformat()}")

            return emails

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des emails: {e}")
            raise

    def _fetch_and_parse_email(self, email_id: bytes) -> Optional[EmailData]:
        """
        Récupère et parse un email spécifique.

        Args:
            email_id: ID de l'email à récupérer.

        Returns:
            EmailData parsé ou None en cas d'erreur.
        """
        try:
            # Récupération de l'email brut (Body PEAK pour ne pas marquer comme lu tout de suite si voulu)
            # Mais ici on utilise (RFC822) qui marque généralement comme lu implicitement selon le serveur.
            # Cependant, Gmail IMAP est particulier. La bonne pratique est de marquer EXPLICITEMENT comme lu après traitement.
            
            status, msg_data = self.imap.fetch(email_id, "(RFC822)")
            if status != "OK":
                logger.error(f"Impossible de récupérer l'email {email_id}")
                return None

            # Parsing du message email
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)

            return self._parse_email(email_message)

        except Exception as e:
            logger.error(f"Erreur lors du fetch de l'email {email_id}: {e}")
            return None

    def _parse_email(self, email_message: Message) -> EmailData:
        """
        Parse un message email en modèle EmailData.

        Args:
            email_message: Message email à parser.

        Returns:
            EmailData avec toutes les informations extraites.
        """
        # Extraction de l'expéditeur
        from_header = email_message.get("From", "")
        from_address, from_name = self._parse_email_address(from_header)

        # Extraction des destinataires
        to_addresses = self._parse_email_list(email_message.get("To", ""))
        cc_addresses = self._parse_email_list(email_message.get("Cc", ""))

        # Extraction du sujet
        subject = self._decode_header(email_message.get("Subject", ""))

        # Extraction de la date
        date_str = email_message.get("Date", "")
        email_date = email.utils.parsedate_to_datetime(date_str)

        # Extraction du message-id
        message_id = email_message.get("Message-ID", "")

        # Extraction du corps (text et html)
        body_text, body_html = self._extract_body(email_message)

        # Extraction des pièces jointes
        attachments = self._extract_attachments(email_message)

        return EmailData(
            message_id=message_id,
            from_address=from_address,
            from_name=from_name,
            to_addresses=to_addresses,
            cc_addresses=cc_addresses,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            date=email_date,
            attachments=attachments,
            is_read=False,
            folder=self.settings.IMAP_LABEL
        )

    def _parse_email_address(self, header: str) -> tuple[str, Optional[str]]:
        """
        Parse une adresse email avec nom optionnel.

        Args:
            header: Header email (ex: "John Doe <john@example.com>").

        Returns:
            Tuple (email, nom) ou (email, None).
        """
        if not header:
            return ("unknown@unknown.com", None)

        # Utilise email.utils pour parser l'adresse
        name, addr = email.utils.parseaddr(header)

        # Décode le nom si nécessaire
        if name:
            name = self._decode_header(name)

        return (addr if addr else "unknown@unknown.com", name if name else None)

    def _parse_email_list(self, header: str) -> List[str]:
        """
        Parse une liste d'adresses email.

        Args:
            header: Header contenant plusieurs emails.

        Returns:
            Liste des adresses email.
        """
        if not header:
            return []

        addresses = email.utils.getaddresses([header])
        return [addr for name, addr in addresses if addr]

    def _decode_header(self, header: str) -> str:
        """
        Décode un header email encodé.

        Args:
            header: Header à décoder.

        Returns:
            String décodé en UTF-8.
        """
        if not header:
            return ""

        decoded_parts = decode_header(header)
        decoded_string = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                # Décode en utilisant l'encodage spécifié ou UTF-8 par défaut
                decoded_string += part.decode(encoding or "utf-8", errors="replace")
            else:
                decoded_string += part

        return decoded_string

    def _extract_body(self, email_message: Message) -> tuple[Optional[str], Optional[str]]:
        """
        Extrait le corps de l'email (text et html).

        Args:
            email_message: Message email.

        Returns:
            Tuple (body_text, body_html).
        """
        body_text = None
        body_html = None

        if email_message.is_multipart():
            # Email multipart (texte + html généralement)
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Ignore les pièces jointes
                if "attachment" in content_disposition:
                    continue

                try:
                    body = part.get_payload(decode=True)
                    if body:
                        charset = part.get_content_charset() or "utf-8"
                        body = body.decode(charset, errors="replace")

                        if content_type == "text/plain" and not body_text:
                            body_text = body
                        elif content_type == "text/html" and not body_html:
                            body_html = body

                except Exception as e:
                    logger.warning(f"Erreur lors du décodage du corps: {e}")
                    continue
        else:
            # Email simple (text ou html seulement)
            try:
                body = email_message.get_payload(decode=True)
                if body:
                    charset = email_message.get_content_charset() or "utf-8"
                    body = body.decode(charset, errors="replace")

                    content_type = email_message.get_content_type()
                    if content_type == "text/plain":
                        body_text = body
                    elif content_type == "text/html":
                        body_html = body
                    else:
                        # Par défaut, considère comme texte
                        body_text = body

            except Exception as e:
                logger.warning(f"Erreur lors du décodage du corps simple: {e}")

        return (body_text, body_html)

    def _extract_attachments(self, email_message: Message) -> List[EmailAttachment]:
        """
        Extrait les pièces jointes de l'email.

        Args:
            email_message: Message email.

        Returns:
            Liste des pièces jointes extraites.
        """
        attachments = []

        if not email_message.is_multipart():
            return attachments

        for part in email_message.walk():
            content_disposition = str(part.get("Content-Disposition", ""))

            # Vérifie si c'est une pièce jointe
            if "attachment" not in content_disposition:
                continue

            try:
                # Récupération du nom du fichier
                filename = part.get_filename()
                if not filename:
                    continue

                filename = self._decode_header(filename)

                # Récupération du contenu
                content = part.get_payload(decode=True)
                if not content:
                    continue

                # Récupération du type MIME
                content_type = part.get_content_type()

                # Calcul de la taille
                size_bytes = len(content)

                # Création de l'objet attachment
                attachment = EmailAttachment(
                    filename=filename,
                    content_type=content_type,
                    size_bytes=size_bytes,
                    content=content
                )

                attachments.append(attachment)
                logger.debug(
                    f"Pièce jointe extraite: {filename} "
                    f"({size_bytes} bytes, {content_type})"
                )

            except Exception as e:
                logger.warning(f"Erreur lors du extraction d'une pièce jointe: {e}")
                continue

        return attachments

    def mark_as_read(self, message_id: str) -> bool:
        """
        Marque un email comme lu via son Message-ID.

        Args:
            message_id: ID du message à marquer.

        Returns:
            bool: True si succès.
        """
        if not self.connected or not self.imap:
            logger.error("Connexion IMAP non établie")
            return False

        try:
            # Recherche de l'email par Message-ID
            # Note: SEARCH HEADER est parfois lent ou non supporté par tous les serveurs IMAP
            status, message_numbers = self.imap.search(
                None,
                f'HEADER Message-ID "{message_id}"'
            )

            if status != "OK" or not message_numbers[0]:
                logger.warning(f"Email avec Message-ID {message_id} non trouvé pour marquage READ")
                return False

            email_id = message_numbers[0].split()[0]

            # Marque comme lu (ajoute le flag \Seen)
            self.imap.store(email_id, "+FLAGS", "\\Seen")
            logger.info(f"Email {message_id} marqué comme lu (SEEN)")
            return True

        except Exception as e:
            logger.error(f"Erreur lors du marquage comme lu: {e}")
            return False

    def disconnect(self):
        """Ferme proprement la connexion IMAP."""
        if self.imap and self.connected:
            try:
                self.imap.close()
                self.imap.logout()
                self.connected = False
                logger.info("Connexion IMAP fermée")
            except Exception as e:
                logger.warning(f"Erreur lors de la fermeture IMAP: {e}")

    def __enter__(self):
        """Context manager: connexion automatique."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: déconnexion automatique."""
        self.disconnect()
