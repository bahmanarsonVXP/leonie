"""
Service d'envoi d'emails via SMTP.

Ce module gère l'envoi d'emails transactionnels et conversationnels
avec support pour les pièces jointes, le HTML et le mode 'Shadow' (Brouillon).
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Optional, Union

from app.config import get_settings

logger = logging.getLogger(__name__)


class SmtpService:
    """
    Service d'envoi d'emails SMTP.
    
    Gère:
    - Connexion SMTP sécurisée (TLS)
    - Envoi HTML/Texte
    - Pièces jointes
    - Mode Shadow (envoi caché au courtier)
    """

    def __init__(self):
        self.settings = get_settings()
        self.smtp_host = self.settings.SMTP_HOST
        self.smtp_port = self.settings.SMTP_PORT
        self.smtp_user = self.settings.SMTP_EMAIL
        self.smtp_alias = self.settings.SMTP_ALIAS or self.settings.SMTP_EMAIL
        self.smtp_password = self.settings.SMTP_PASSWORD
        self.from_name = self.settings.SMTP_FROM_NAME

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Union[str, Path]]] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        message_id_header: Optional[str] = None,
        in_reply_to_header: Optional[str] = None,
        is_shadow_mode: bool = False,
        shadow_recipient: Optional[str] = None
    ) -> bool:
        """
        Envoie un email via SMTP.

        Args:
            to_email: Destinataire principal.
            subject: Sujet de l'email.
            html_content: Corps HTML.
            text_content: Corps texte (fallback). Si None, généré depuis HTML.
            attachments: Liste de chemins vers les fichiers à joindre.
            cc_emails: Liste des emails en copie.
            bcc_emails: Liste des emails en copie cachée.
            reply_to: Adresse Reply-To (pour threading).
            message_id_header: Header Message-ID (optionnel).
            in_reply_to_header: Header In-Reply-To (pour threading).
            is_shadow_mode: Si True, force l'envoi au courtier/admin UNIQUEMENT.
            shadow_recipient: L'email réel qui recevra le message en mode Shadow (Courtier).

        Returns:
            bool: True si envoi réussi.
        """
        try:
            # Gestion du mode Shadow (Redirection de sécurité)
            original_to = to_email
            if is_shadow_mode:
                # En mode Shadow, on n'envoie JAMAIS au client
                # On redirige vers le destinataire spécifié (Courtier) ou l'Admin par défaut
                redirect_to = shadow_recipient or self.settings.ADMIN_EMAIL
                
                # BUGFIX: Ne jamais utiliser reply_to comme redirection car c'est souvent le client !
                
                logger.info(f"🔒 MODE SHADOW: Redirection de {original_to} vers {redirect_to}")
                to_email = redirect_to
                subject = f"[SHADOW] {subject}"
                html_content = f"""
                <div style="background-color: #fff3cd; color: #856404; padding: 10px; margin-bottom: 20px; border: 1px solid #ffeeba;">
                    <strong>MODE SHADOW / BROUILLON</strong><br>
                    Ceci est une proposition de réponse pour : {original_to}<br>
                    Sujet original : {subject.replace('[SHADOW] ', '')}
                </div>
                <hr>
                {html_content}
                """

            # Création du message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.smtp_alias}>"
            msg["To"] = to_email
            
            if cc_emails:
                msg["Cc"] = ", ".join(cc_emails)
            
            if reply_to:
                msg["Reply-To"] = reply_to

            # Headers spécifiques pour le threading (Gmail)
            if message_id_header:
                msg["Message-ID"] = message_id_header
            if in_reply_to_header:
                msg["In-Reply-To"] = in_reply_to_header
                msg["References"] = in_reply_to_header

            # Corps du message
            # Version texte par défaut si non fournie
            if not text_content:
                text_content = "Veuillez activer l'affichage HTML pour voir ce message."
            
            part_text = MIMEText(text_content, "plain")
            part_html = MIMEText(html_content, "html")

            msg.attach(part_text)
            msg.attach(part_html)

            # Pièces jointes
            if attachments:
                for file_path in attachments:
                    path = Path(file_path)
                    if not path.exists():
                        logger.warning(f"Pièce jointe introuvable: {path}")
                        continue
                    
                    try:
                        with open(path, "rb") as attachment:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename= {path.name}",
                        )
                        msg.attach(part)
                    except Exception as e:
                        logger.error(f"Erreur attachement fichier {path}: {e}")

            # Connexion et envoi
            # Utilisation de SMTP simple avec starttls ensuite (port 587)
            # FIX: Force IPv4 pour éviter "Network is unreachable" sur Railway (qui tente IPv6)
            try:
                # Résolution manuelle IPv4
                import socket
                addr_info = socket.getaddrinfo(self.smtp_host, self.smtp_port, socket.AF_INET, socket.SOCK_STREAM)
                smtp_ip = addr_info[0][4][0]
                logger.info(f"Résolution SMTP IPv4: {self.smtp_host} -> {smtp_ip}")
                
                server = smtplib.SMTP()
                server.connect(smtp_ip, self.smtp_port)
                # CRITIQUE: Remettre le hostname original pour que la validation SSL (starttls) fonctionne !
                server._host = self.smtp_host 
            except Exception as e:
                logger.warning(f"Échec force IPv4, fallback standard: {e}")
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)

            server.set_debuglevel(0) # Mettre à 1 pour debug
            
            server.ehlo() # Identification initiale
            server.starttls() # Sécurisation TLS
            server.ehlo() # Ré-identification chiffrée
            
            server.login(self.smtp_user, self.smtp_password)
            
            # Liste complète des destinataires
            recipients = [to_email]
            if cc_emails:
                recipients.extend(cc_emails)
            if bcc_emails:
                recipients.extend(bcc_emails)

            server.sendmail(self.smtp_user, recipients, msg.as_string())
            server.quit()

            logger.info(
                f"Email envoyé avec succès à {to_email}",
                extra={
                    "subject": subject,
                    "shadow_mode": is_shadow_mode,
                    "attachments": len(attachments) if attachments else 0
                }
            )
            return True

        except Exception as e:
            logger.error(
                f"Erreur envoi SMTP: {e}",
                extra={"to": to_email, "subject": subject},
                exc_info=True
            )
            return False
