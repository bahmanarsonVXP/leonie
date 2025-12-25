"""
Service de Gestion du Contexte (Mémoire).

Gère la lecture et la mise à jour de la "mémoire" dossier dans Supabase.
Utilise Mistral pour synthétiser les nouveaux événements dans le résumé narratif.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Optional

from app.services.mistral import MistralService
from app.utils.db import get_dossier_context, update_dossier_context, create_dossier_context

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Gère la mémoire et l'état des dossiers.
    """
    
    def __init__(self):
        self.mistral = MistralService()

    async def get_or_init_context(self, client_id: str) -> Dict:
        """Récupère le contexte ou l'initialise s'il n'existe pas."""
        context = get_dossier_context(client_id)
        if not context:
            logger.info(f"Création contexte initial pour client {client_id}")
            context = create_dossier_context(client_id)
        return context

    async def update_context_with_email(
        self, 
        client_id: str, 
        email_content: str, 
        action_type: str
    ) -> Dict:
        """
        Met à jour le contexte avec un nouvel email entrant.
        Appelle Mistral pour mettre à jour le résumé narratif.
        """
        context = await self.get_or_init_context(client_id)
        current_summary = context.get("summary") or "Dossier initié. Pas d'historique."
        
        # Appel Mistral pour fusionner le résumé
        new_summary = await self.mistral.update_narrative_context(
            current_summary, 
            new_event=f"Email reçu ('{action_type}'): {email_content[:500]}..."
        )
        
        # Update DB
        updates = {
            "summary": new_summary,
            "last_update": datetime.now().isoformat()
        }
        
        return update_dossier_context(client_id, updates)
