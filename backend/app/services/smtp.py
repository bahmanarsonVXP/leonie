"""
Service d'envoi d'emails via Resend (Remplacement SMTP).

Ce module gère l'envoi d'emails transactionnels via l'API Resend
pour contourner les blocages SMTP de Railway.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Union

import resend
from app.config import get_settings

logger = logging.getLogger(__name__)


class SmtpService:
    """
    Service d'envoi d'emails (via Resend).
    
    Le nom 'SmtpService' est conservé pour la compatibilité avec le reste du code,
    mais l'implémentation utilise l'API HTTP de Resend.
    """

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.RESEND_API_KEY
        
        if self.api_key:
            resend.api_key = self.api_key
        else:
            logger.warning("⚠️ RESEND_API_KEY non définie. Les emails ne partiront pas.")

        self.from_email = self.settings.RESEND_FROM_EMAIL

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
        Envoie un email via l'API Resend.

        Args:
            to_email: Destinataire principal.
            subject: Sujet de l'email.
            html_content: Corps HTML.
            text_content: Corps texte (optionnel).
            attachments: Liste de chemins vers les fichiers à joindre.
            cc_emails: Liste des emails en copie.
            bcc_emails: Liste des emails en copie cachée.
            reply_to: Adresse Reply-To.
            message_id_header: (Non supporté par Resend nativement, ignoré).
            in_reply_to_header: (Non supporté par Resend nativement, ignoré).
            is_shadow_mode: Si True, force l'envoi au courtier/admin UNIQUEMENT.
            shadow_recipient: L'email réel qui recevra le message en mode Shadow.

        Returns:
            bool: True si envoi réussi.
        """
        if not self.api_key:
            logger.error("❌ Echec envoi: API Key Resend manquante")
            return False

        try:
            # Gestion du mode Shadow (Redirection de sécurité)
            original_to = to_email
            
            # Logique Shadow Mode conservée
            if is_shadow_mode:
                redirect_to = shadow_recipient or self.settings.ADMIN_EMAIL
                logger.info(f"🔒 MODE SHADOW (Resend): Redirection de {original_to} vers {redirect_to}")
                to_email = redirect_to
                subject = f"[SHADOW] {subject}"
                html_content = f"""
                <div style="background-color: #fff3cd; color: #856404; padding: 10px; margin-bottom: 20px; border: 1px solid #ffeeba;">
                    <strong>MODE SHADOW / BROUILLON (Resend)</strong><br>
                    Ceci est une proposition de réponse pour : {original_to}<br>
                    Sujet original : {subject.replace('[SHADOW] ', '')}
                </div>
                <hr>
                {html_content}
                """

            # Préparation des paramètres Resend
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }

            if text_content:
                params["text"] = text_content
            
            if cc_emails:
                params["cc"] = cc_emails
            
            if bcc_emails:
                params["bcc"] = bcc_emails
            
            if reply_to:
                params["reply_to"] = reply_to

            # Gestion des pièces jointes pour Resend
            # Resend attend une liste de dicts: {"filename": "x", "content": list[int]}
            if attachments:
                resend_attachments = []
                for file_path in attachments:
                    path = Path(file_path)
                    if not path.exists():
                        logger.warning(f"Pièce jointe introuvable: {path}")
                        continue
                    
                    try:
                        with open(path, "rb") as f:
                            # Resend Python SDK requiert le contenu en liste d'entiers (bytes list)
                            content_bytes = list(f.read())
                            resend_attachments.append({
                                "filename": path.name,
                                "content": content_bytes
                            })
                    except Exception as e:
                        logger.error(f"Erreur lecture pièce jointe {path}: {e}")
                
                if resend_attachments:
                    params["attachments"] = resend_attachments

            # Envoi effectif
            logger.info(f"Envoi email via Resend à {to_email}...")
            response = resend.Emails.send(params)
            
            # Vérification basique du retour (Resend retourne un dict avec 'id' sur succès)
            if response and "id" in response:
                logger.info(f"✅ Email envoyé via Resend! ID: {response['id']}")
                return True
            else:
                logger.error(f"❌ Réponse inattendue de Resend: {response}")
                return False

        except Exception as e:
            logger.error(
                f"Erreur CRITIQUE envoi Resend: {e}",
                extra={"to": to_email, "subject": subject},
                exc_info=True
            )
            return False
