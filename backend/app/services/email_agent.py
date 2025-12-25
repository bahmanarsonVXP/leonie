"""
Orchestrateur Principal : Agent Email (Léonie).

Coordonne tous les services pour gérer le cycle de vie complet d'un email entrant :
Réception -> Analyse -> Documents -> Contexte -> Réponse (Shadow/Whisper).
"""

import logging
import asyncio
from typing import Optional

from app.models.email import EmailData, EmailClassification, EmailAction
from app.services.mistral import MistralService
from app.services.context_manager import ContextManager
from app.services.document_orchestrator import DocumentOrchestrator
from app.services.response_generator import ResponseGenerator
from app.services.smtp import SmtpService
from app.services.client_identifier import ClientIdentifier
from app.services.drive import DriveManager
from app.utils.db import (
    get_client_by_email, 
    get_courtier_by_email, 
    get_courtier_by_id, 
    create_dossier_context,
    log_activity
)

logger = logging.getLogger(__name__)

class EmailAgent:
    """
    L'intelligence centrale de Léonie.
    """

    def __init__(self):
        self.mistral = MistralService()
        self.context_mgr = ContextManager()
        self.doc_orchestrator = DocumentOrchestrator()
        self.response_gen = ResponseGenerator()
        self.smtp = SmtpService()
        self.drive_manager = DriveManager() 

    async def process_incoming_email(self, email: EmailData) -> bool:
        """
        Traite un email entrant de A à Z.
        """
        logger.info(f"🤖 Agent: Traitement email {email.subject} de {email.from_address}")

        # 1. Identification (Courtier ou Client ?)
        client = get_client_by_email(email.from_address)
        courtier = None
        is_new_client = False

        if client:
            # Client existant
            courtier_id = client['courtier_id']
            courtier = get_courtier_by_id(courtier_id)
            logger.info(f"✅ Client existant identifié: {client.get('prenom')} {client.get('nom')}")
        else:

            # Nouveau Client potentiel ou Forward Courtier
            logger.info("Email d'un expéditeur inconnu (non-client). Vérification si c'est un courtier...")

            # Scenario A: Le sender EST le courtier (Forward)
            sender_courtier = get_courtier_by_email(email.from_address)
            if sender_courtier:
                courtier = sender_courtier
                logger.info(f"✅ Sender identifié comme Courtier: {courtier.get('nom')}. Mode 'Forward/Instruction'.")
                # On force la création nouveau client car c'est le courtier qui nous l'envoie
                # Le body de l'email contiendra les infos du client
                is_new_client = True
            
            else:
                # Scenario B: Le sender est un prospect inconnu
                # Recherche du courtier via les destinataires de l'email (ex: leonie@voxperience.com)
                for recipient in email.to_addresses + email.cc_addresses:
                    possible_courtier = get_courtier_by_email(recipient)
                    if possible_courtier:
                        courtier = possible_courtier
                        logger.info(f"✅ Courtier identifié via destinataire {recipient}: {courtier.get('nom')}")
                        break
                
                if not courtier:
                    logger.warning(
                        "❌ Impossible d'identifier le courtier (ni sender, ni destinataire). "
                        "L'email est ignoré car orphelin."
                    )
                    return False
                
                is_new_client = True

        # 2. Classification Intention (Mistral)
        classification = await self.mistral.classify_email(
            email, 
            client_exists=(not is_new_client), 
            courtier=courtier
        )
        logger.info(f"Agent: Classification = {classification.action} ({classification.confiance})")

        # Gestion Nouveau Client
        if is_new_client:
            try:
                # Si le sender a été identifié comme courtier (Scenario A), on doit l'exclure
                # pour éviter qu'il soit détecté comme client.
                sender_is_broker = False
                if email.from_address:
                     sender_courtier_check = get_courtier_by_email(email.from_address)
                     if sender_courtier_check:
                         sender_is_broker = True

                logger.info(f"🆕 Création d'un nouveau client... (Exclude Sender Mode: {sender_is_broker})")
                
                client = ClientIdentifier.create_client_from_email_and_classification(
                    email,
                    courtier,
                    classification.model_dump(),
                    self.drive_manager,
                    exclude_sender=sender_is_broker
                )
                logger.info(f"🎉 Nouveau client créé : {client.get('id')}")
                
                # Initialisation contexte
                create_dossier_context(client['id'])

            except Exception as e:
                logger.error(f"❌ Erreur création client: {e}", exc_info=True)
                return False

        # À ce stade on A un client et un courtier
        client_id = client['id']
        courtier_id = courtier['id']

        # 3. Traitement Documents (Si pièces jointes)
        if email.attachments:
            processed_docs = self.doc_orchestrator.process_attachments(
                email.attachments, 
                client,  # Pass full client object
                courtier_id
            )
        
        # 4. Mise à jour Mémoire (Context)
        narrative_event = f"Reçu email: {classification.resume}. "
        if processed_docs:
            doc_names = ", ".join([d['final_name'] for d in processed_docs])
            narrative_event += f"Documents traités : {doc_names}."
        
        context = await self.context_mgr.update_context_with_email(
            client_id, 
            email.body_text, 
            classification.action.value
        )

        # 5. Décision Action (Shadow / Whisper)
        should_reply = True 
        
        if should_reply:
            # Générer brouillon
            draft_html = await self.response_gen.generate_draft_reply(
                email, 
                context, 
                courtier
            )
            
            # Envoyer en mode Shadow
            success = self.smtp.send_email(
                to_email=client['email_principal'],
                subject=f"RE: {email.subject}",
                html_content=draft_html,
                reply_to=client['email_principal'],
                is_shadow_mode=True,
                shadow_recipient=courtier['email']
            )
            
            if success:
                log_activity(
                    "agent_whisper", 
                    {"draft_subject": email.subject}, 
                    client_id=client_id, 
                    courtier_id=courtier_id
                )
        
        return True
