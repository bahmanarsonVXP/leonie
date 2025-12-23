"""
Router qui dispatche les emails classifiés vers les workflows appropriés.

Ce module route les emails selon leur classification Mistral AI
vers les handlers de traitement appropriés.

NOTE TEMPORAIRE (Session 9):
    Les jobs sont appelés directement (mode synchrone) au lieu d'être
    enqueued dans Redis. Ceci est temporaire en attendant l'installation
    de Redis sur Railway.

    CIBLE FINALE : Redis Queue (RQ) avec workers asynchrones
    Une fois Redis installé, décommenter les lignes Redis et retirer
    les appels directs.
"""

import logging
from typing import Dict

from app.models.email import EmailAction, EmailClassification, EmailData

# TEMPORAIRE: Import direct des jobs au lieu de Redis
from app.workers.jobs import (
    process_nouveau_dossier,
    process_envoi_documents,
    process_modifier_liste
)

# TODO: Réactiver une fois Redis installé sur Railway
# from app.utils.redis_client import get_queue

logger = logging.getLogger(__name__)


class EmailRouter:
    """
    Dispatche les emails vers les workflows appropriés selon leur classification.

    Chaque type d'EmailAction correspond à un workflow spécifique
    qui sera implémenté dans les prochaines sessions.
    """

    @staticmethod
    async def route(
        email: EmailData,
        classification: EmailClassification,
        courtier: Dict
    ) -> Dict:
        """
        Route l'email vers le workflow approprié.

        Args:
            email: Email parsé
            classification: Classification Mistral
            courtier: Courtier identifié (dict Supabase)

        Returns:
            Résultat du traitement

        Example:
            >>> result = await EmailRouter.route(email, classification, courtier)
            >>> if result["status"] == "success":
            ...     print(f"Traité: {result['message']}")
        """
        logger.info(
            f"Routing email vers workflow: {classification.action.value}",
            extra={
                "email_id": email.message_id,
                "action": classification.action.value,
                "confiance": classification.confiance
            }
        )

        match classification.action:
            case EmailAction.NOUVEAU_DOSSIER:
                return await EmailRouter._handle_nouveau_dossier(
                    email, classification, courtier
                )

            case EmailAction.ENVOI_DOCUMENTS:
                return await EmailRouter._handle_envoi_documents(
                    email, classification, courtier
                )

            case EmailAction.MODIFIER_LISTE:
                return await EmailRouter._handle_modifier_liste(
                    email, classification, courtier
                )

            case EmailAction.QUESTION:
                return await EmailRouter._handle_question(
                    email, classification, courtier
                )

            case EmailAction.CONTEXTE:
                return await EmailRouter._handle_contexte(
                    email, classification, courtier
                )

    @staticmethod
    async def _handle_nouveau_dossier(
        email: EmailData,
        classification: EmailClassification,
        courtier: Dict
    ) -> Dict:
        """
        Workflow : Création d'un nouveau dossier client.

        TEMPORAIRE (Session 9): Appel direct synchrone au lieu de Redis Queue.

        CIBLE FINALE: Enqueue un job RQ prioritaire pour créer le dossier client,
        la structure Drive, et initialiser la liste des pièces attendues.

        Args:
            email: Email contenant la demande
            classification: Classification avec details du client
            courtier: Courtier propriétaire du dossier

        Returns:
            Dict avec status "success" et résultat du traitement
        """
        logger.info(
            "Traitement nouveau dossier (DIRECT - sans Redis)",
            extra={
                "courtier_id": courtier.get("id"),
                "client_nom": classification.details.get("client_nom")
            }
        )

        # TEMPORAIRE: Appel direct au lieu de enqueue
        # Une fois Redis installé, décommenter le bloc ci-dessous et retirer l'appel direct

        # === CODE CIBLE (Redis) - À RÉACTIVER ===
        # queue = get_queue("high")  # Priorité haute pour nouveaux dossiers
        # job = queue.enqueue(
        #     'app.workers.jobs.process_nouveau_dossier',
        #     courtier_id=courtier.get("id"),
        #     email_data=email.model_dump(mode='json'),
        #     classification=classification.model_dump(mode='json'),
        #     job_timeout=300  # 5 minutes max
        # )
        # logger.info("Job nouveau dossier enqueued", extra={"job_id": job.id})
        # return {
        #     "status": "enqueued",
        #     "action": "nouveau_dossier",
        #     "job_id": job.id,
        #     "message": "Job de création de dossier enqueued"
        # }
        # === FIN CODE CIBLE ===

        # Appel direct (TEMPORAIRE)
        try:
            result = process_nouveau_dossier(
                courtier_id=courtier.get("id"),
                email_data=email.model_dump(mode='json'),
                classification=classification.model_dump(mode='json')
            )

            logger.info(
                "Nouveau dossier traité avec succès",
                extra={"result": result}
            )

            return {
                "status": "success",
                "action": "nouveau_dossier",
                "result": result,
                "message": "Dossier créé avec succès"
            }

        except Exception as e:
            logger.error(
                f"Erreur lors de la création du dossier: {e}",
                exc_info=True
            )
            return {
                "status": "error",
                "action": "nouveau_dossier",
                "error": str(e),
                "message": f"Erreur: {str(e)}"
            }

    @staticmethod
    async def _handle_envoi_documents(
        email: EmailData,
        classification: EmailClassification,
        courtier: Dict
    ) -> Dict:
        """
        Workflow : Traitement de documents envoyés pour un dossier existant.

        TEMPORAIRE (Session 9): Appel direct synchrone au lieu de Redis Queue.

        CIBLE FINALE: Enqueue un job RQ pour traiter les pièces jointes, les classifier,
        les convertir en PDF, les compresser, et les uploader sur Drive.

        Args:
            email: Email avec pièces jointes
            classification: Classification avec types détectés
            courtier: Courtier propriétaire

        Returns:
            Dict avec status "success" et résultat du traitement
        """
        nb_attachments = len(email.attachments)

        logger.info(
            "Traitement envoi documents (DIRECT - sans Redis)",
            extra={
                "courtier_id": courtier.get("id"),
                "nb_attachments": nb_attachments
            }
        )

        # TEMPORAIRE: Appel direct au lieu de enqueue
        # Une fois Redis installé, décommenter le bloc ci-dessous et retirer l'appel direct

        # === CODE CIBLE (Redis) - À RÉACTIVER ===
        # queue = get_queue("default")  # Priorité normale
        # job = queue.enqueue(
        #     'app.workers.jobs.process_envoi_documents',
        #     courtier_id=courtier.get("id"),
        #     email_data=email.model_dump(mode='json'),
        #     classification=classification.model_dump(mode='json'),
        #     job_timeout=600  # 10 minutes max
        # )
        # logger.info("Job envoi documents enqueued", extra={"job_id": job.id})
        # return {
        #     "status": "enqueued",
        #     "action": "envoi_documents",
        #     "job_id": job.id,
        #     "nb_pieces": nb_attachments,
        #     "message": f"Job de traitement de {nb_attachments} documents enqueued"
        # }
        # === FIN CODE CIBLE ===

        # Appel direct (TEMPORAIRE)
        try:
            result = process_envoi_documents(
                courtier_id=courtier.get("id"),
                email_data=email.model_dump(mode='json'),
                classification=classification.model_dump(mode='json')
            )

            logger.info(
                "Documents traités avec succès",
                extra={"result": result, "nb_pieces": nb_attachments}
            )

            return {
                "status": "success",
                "action": "envoi_documents",
                "result": result,
                "nb_pieces": nb_attachments,
                "message": f"{nb_attachments} document(s) traité(s) avec succès"
            }

        except Exception as e:
            logger.error(
                f"Erreur lors du traitement des documents: {e}",
                exc_info=True
            )
            return {
                "status": "error",
                "action": "envoi_documents",
                "error": str(e),
                "nb_pieces": nb_attachments,
                "message": f"Erreur: {str(e)}"
            }

    @staticmethod
    async def _handle_modifier_liste(
        email: EmailData,
        classification: EmailClassification,
        courtier: Dict
    ) -> Dict:
        """
        Workflow : Modification de la liste des pièces attendues pour un dossier.

        TEMPORAIRE (Session 9): Appel direct synchrone au lieu de Redis Queue.

        CIBLE FINALE: Enqueue un job RQ pour modifier dynamiquement la checklist d'un dossier
        (ajouter ou retirer des pièces attendues).

        Use case:
            Courtier envoie "Pour le dossier Martin, ajouter aussi : attestation employeur et RIB"

        Args:
            email: Email de demande de modification
            classification: Classification avec pièces à ajouter/retirer
            courtier: Courtier demandeur

        Returns:
            Dict avec status "success" et résultat du traitement
        """
        logger.info(
            "Modification liste (DIRECT - sans Redis)",
            extra={
                "courtier_id": courtier.get("id"),
                "client_nom": classification.details.get("client_nom")
            }
        )

        # TEMPORAIRE: Appel direct au lieu de enqueue
        # Une fois Redis installé, décommenter le bloc ci-dessous et retirer l'appel direct

        # === CODE CIBLE (Redis) - À RÉACTIVER ===
        # queue = get_queue("default")  # Priorité normale
        # job = queue.enqueue(
        #     'app.workers.jobs.process_modifier_liste',
        #     courtier_id=courtier.get("id"),
        #     email_data=email.model_dump(mode='json'),
        #     classification=classification.model_dump(mode='json'),
        #     job_timeout=120  # 2 minutes max
        # )
        # logger.info("Job modifier liste enqueued", extra={"job_id": job.id})
        # return {
        #     "status": "enqueued",
        #     "action": "modifier_liste",
        #     "job_id": job.id,
        #     "message": "Job de modification de liste enqueued"
        # }
        # === FIN CODE CIBLE ===

        # Appel direct (TEMPORAIRE)
        try:
            result = process_modifier_liste(
                courtier_id=courtier.get("id"),
                email_data=email.model_dump(mode='json'),
                classification=classification.model_dump(mode='json')
            )

            logger.info(
                "Liste modifiée avec succès",
                extra={"result": result}
            )

            return {
                "status": "success",
                "action": "modifier_liste",
                "result": result,
                "message": "Liste des pièces modifiée avec succès"
            }

        except Exception as e:
            logger.error(
                f"Erreur lors de la modification de la liste: {e}",
                exc_info=True
            )
            return {
                "status": "error",
                "action": "modifier_liste",
                "error": str(e),
                "message": f"Erreur: {str(e)}"
            }

    @staticmethod
    async def _handle_question(
        email: EmailData,
        classification: EmailClassification,
        courtier: Dict
    ) -> Dict:
        """
        Workflow : Gestion des questions du courtier.

        Étapes prévues:
        1. Enregistrer la question dans logs_activite
        2. Si urgent → notification admin immédiate
        3. Sinon → ajouter au rapport quotidien

        Use cases:
            - "Je n'arrive pas à ouvrir ce document"
            - "Le système a classé ce doc en mauvaise catégorie"
            - "Comment ajouter un nouveau type de pièce ?"

        Args:
            email: Email contenant la question
            classification: Classification avec sujet et urgence
            courtier: Courtier demandeur

        Returns:
            Dict avec status et action prise

        TODO:
            Session 7+: Implémenter gestion questions + notifications
        """
        urgent = classification.details.get("urgent", False)

        logger.info(
            "TODO: Question courtier",
            extra={
                "resume": classification.resume,
                "urgent": urgent,
                "sujet": classification.details.get("sujet")
            }
        )

        return {
            "status": "todo",
            "action": "question",
            "urgent": urgent,
            "message": "Gestion des questions non implémentée (TODO Session 7+)"
        }

    @staticmethod
    async def _handle_contexte(
        email: EmailData,
        classification: EmailClassification,
        courtier: Dict
    ) -> Dict:
        """
        Workflow : Archivage d'emails contextuels.

        Étapes:
        1. Enregistrer dans logs_activite avec categorie
        2. Pas d'action supplémentaire requise

        Use cases:
            - Email en CC pour information
            - Suivi client transféré en copie
            - Notifications système

        Args:
            email: Email contextuel
            classification: Classification avec catégorie
            courtier: Courtier lié

        Returns:
            Dict avec status d'archivage

        TODO:
            Session 7+: Implémenter archivage dans logs
        """
        categorie = classification.details.get("categorie", "autre")

        logger.info(
            "TODO: Stocker contexte",
            extra={
                "resume": classification.resume,
                "categorie": categorie
            }
        )

        return {
            "status": "todo",
            "action": "contexte",
            "categorie": categorie,
            "message": "Archivage contexte non implémenté (TODO Session 7+)"
        }
