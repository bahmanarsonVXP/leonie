"""
Service de Génération de Réponses (AI Response Generator).

Utilise Mistral AI pour rédiger des brouillons de réponses emails
basés sur le contexte du dossier et le style du courtier.
"""

import logging
from typing import Dict, Optional

from app.services.mistral import MistralService
from app.models.email import EmailData

logger = logging.getLogger(__name__)

class ResponseGenerator:
    """
    Rédacteur automatique d'emails.
    """
    
    def __init__(self):
        self.mistral = MistralService()

    async def generate_draft_reply(
        self,
        email: EmailData,
        context: Dict,
        courtier_info: Dict
    ) -> str:
        """
        Génère un brouillon de réponse.
        
        Args:
            email: Email reçu
            context: Contexte du dossier (résumé narratif)
            courtier_info: Infos du courtier (pour signature)
            
        Returns:
            Corps HTML suggéré pour l'email.
        """
        client_summary = context.get("summary", "Pas d'historique.")
        
        prompt = f"""
        Tu es l'assistant personnel du courtier {courtier_info.get("prenom")} {courtier_info.get("nom")}.
        
        CONTEXTE DU DOSSIER :
        {client_summary}
        
        EMAIL REÇU DU CLIENT :
        Sujet: {email.subject}
        Corps: {email.body_text}
        
        TA VISION :
        Rédige une réponse professionnelle, empathique et rassurante.
        Si des documents ont été reçus, confirme la réception.
        Si des documents manquent (selon le contexte), fais un rappel gentil.
        Ton : Professionnel mais chaleureux.
        
        Génère uniquement le CORPS de l'email (en HTML simple, <p>, <br>), sans en-têtes.
        Signe avec le Prénom du courtier.
        """
        
        # Appel Mistral (on réutilise classify_email_sync logique ou méthode générique)
        # Pour l'instant on suppose une méthode generate_text dans mistral.py
        # TODO: Ajouter generate_text à MistralService
        
        return await self.mistral.generate_text(prompt)
