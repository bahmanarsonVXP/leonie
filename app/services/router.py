"""
Router qui dispatche les emails classifiés vers les workflows appropriés.

Ce module route les emails selon leur classification Mistral AI
vers les handlers de traitement appropriés.
"""

import logging
from typing import Dict

from app.models.email import EmailAction, EmailClassification, EmailData

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

        Étapes prévues (Session 4+):
        1. Extraire infos client depuis classification.details
        2. Créer le client dans Supabase (table clients)
        3. Créer le dossier Google Drive
        4. Initialiser la liste des pièces attendues selon type_pret
        5. Logger l'activité
        6. Envoyer email de confirmation au courtier

        Args:
            email: Email contenant la demande
            classification: Classification avec details du client
            courtier: Courtier propriétaire du dossier

        Returns:
            Dict avec status et détails de création

        TODO:
            Session 4: Implémenter création dossier + Drive
        """
        logger.info(
            "TODO: Créer nouveau dossier",
            extra={
                "details": classification.details,
                "courtier_id": courtier.get("id")
            }
        )

        return {
            "status": "todo",
            "action": "nouveau_dossier",
            "message": "Création de nouveau dossier non implémentée (TODO Session 4)"
        }

    @staticmethod
    async def _handle_envoi_documents(
        email: EmailData,
        classification: EmailClassification,
        courtier: Dict
    ) -> Dict:
        """
        Workflow : Traitement de documents envoyés pour un dossier existant.

        Étapes prévues (Session 5+):
        1. Identifier le client (via email ou mention dans le corps)
        2. Pour chaque pièce jointe:
            a. Extraire le texte (OCR si image, PDF text extraction)
            b. Classifier avec Mistral (type de pièce)
            c. Vérifier duplicata (hash)
            d. Uploader sur Google Drive
            e. Enregistrer dans pieces_dossier
        3. Mettre à jour progression du dossier
        4. Logger l'activité
        5. Si dossier complet → notification courtier

        Args:
            email: Email avec pièces jointes
            classification: Classification avec types détectés
            courtier: Courtier propriétaire

        Returns:
            Dict avec status et statistiques de traitement

        TODO:
            Session 5: Implémenter traitement documents + OCR + Mistral classification
        """
        nb_attachments = len(email.attachments)

        logger.info(
            "TODO: Traiter documents",
            extra={
                "nb_attachments": nb_attachments,
                "types_detectes": classification.details.get("types_detectes", [])
            }
        )

        return {
            "status": "todo",
            "action": "envoi_documents",
            "nb_pieces": nb_attachments,
            "message": f"Traitement de {nb_attachments} documents non implémenté (TODO Session 5)"
        }

    @staticmethod
    async def _handle_modifier_liste(
        email: EmailData,
        classification: EmailClassification,
        courtier: Dict
    ) -> Dict:
        """
        Workflow : Modification de la liste des pièces attendues pour un dossier.

        Étapes prévues (Session 6+):
        1. Identifier le client via classification.details
        2. Récupérer les pièces à ajouter/retirer
        3. Mettre à jour la checklist du dossier
        4. Logger l'activité
        5. Confirmation au courtier

        Use case:
            Courtier envoie "Pour le dossier Martin, ajouter aussi : attestation employeur et RIB"

        Args:
            email: Email de demande de modification
            classification: Classification avec pièces à ajouter/retirer
            courtier: Courtier demandeur

        Returns:
            Dict avec status et modifications effectuées

        TODO:
            Session 6: Implémenter modification dynamique de checklist
        """
        logger.info(
            "TODO: Modifier liste pièces",
            extra={
                "details": classification.details,
                "client_nom": classification.details.get("client_nom")
            }
        )

        return {
            "status": "todo",
            "action": "modifier_liste",
            "message": "Modification de liste non implémentée (TODO Session 6)"
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
