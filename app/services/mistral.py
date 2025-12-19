"""
Service d'appel à l'API Mistral AI pour classification des emails.

Ce module gère la classification des emails avec Mistral AI et l'extraction
d'informations structurées selon l'intention du courtier.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional

from mistralai import Mistral

from app.config import get_settings
from app.models.courtier import Courtier
from app.models.email import EmailAction, EmailClassification, EmailData

logger = logging.getLogger(__name__)


class MistralService:
    """
    Service d'appel à l'API Mistral AI.

    Gère la classification des emails et l'extraction d'informations
    pour déterminer l'action appropriée à mener.
    """

    def __init__(self):
        """Initialise le service Mistral avec les settings."""
        self.settings = get_settings()
        self.client = Mistral(api_key=self.settings.MISTRAL_API_KEY)
        self.model_chat = self.settings.MISTRAL_MODEL_CHAT
        self.model_vision = self.settings.MISTRAL_MODEL_VISION

        logger.info(
            f"MistralService initialisé avec modèle chat: {self.model_chat}"
        )

    async def classify_email(
        self,
        email: EmailData,
        courtier: Dict,
        client_exists: bool = False
    ) -> EmailClassification:
        """
        Analyse un email et détermine l'action à mener.

        Utilise Mistral pour comprendre l'intention du courtier
        et extraire les informations pertinentes.

        Args:
            email: Email parsé.
            courtier: Courtier identifié (dict Supabase).
            client_exists: True si le client existe déjà en base de données.

        Returns:
            EmailClassification avec action, résumé, confiance, détails.

        Raises:
            Exception: Si l'appel Mistral échoue après 3 tentatives.
        """
        logger.info(
            f"Classification email via Mistral",
            extra={
                "email_subject": email.subject,
                "courtier_email": courtier.get("email"),
                "client_exists": client_exists
            }
        )

        # Construire le prompt
        prompt = self._build_classification_prompt(email, courtier, client_exists)

        # Appel Mistral avec retry
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                # Appel API Mistral
                response = await self.client.chat.complete_async(
                    model=self.model_chat,
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1  # Précision maximale
                )

                # Parser la réponse JSON
                result_text = response.choices[0].message.content
                logger.debug(f"Réponse Mistral brute: {result_text}")

                result = json.loads(result_text)

                # Valider avec Pydantic
                classification = EmailClassification(**result)

                # Logger le résultat
                logger.info(
                    f"Email classifié avec succès",
                    extra={
                        "action": classification.action.value,
                        "confiance": classification.confiance,
                        "resume": classification.resume
                    }
                )

                return classification

            except json.JSONDecodeError as e:
                logger.error(
                    f"Erreur parsing JSON Mistral (tentative {attempt}/{max_retries}): {e}",
                    extra={"response": result_text if 'result_text' in locals() else None}
                )
                if attempt == max_retries:
                    # Fallback : retourner classification par défaut
                    return self._get_fallback_classification(email)
                await asyncio.sleep(1 * attempt)  # Backoff

            except Exception as e:
                logger.error(
                    f"Erreur appel Mistral (tentative {attempt}/{max_retries}): {e}"
                )
                if attempt == max_retries:
                    return self._get_fallback_classification(email)
                await asyncio.sleep(2 ** attempt)  # Backoff exponentiel

    def _get_system_prompt(self) -> str:
        """
        Prompt système définissant le rôle de Léonie.

        Returns:
            Prompt système complet avec exemples.
        """
        return """Tu es Léonie, assistante IA pour courtiers en prêts immobiliers et professionnels.

Ton rôle est d'analyser les emails que les courtiers reçoivent de leurs clients et de déterminer quelle action effectuer.

Tu dois classifier chaque email dans UNE de ces catégories :

1. NOUVEAU_DOSSIER : Le courtier initie un nouveau dossier pour un client
   - Indices : "nouveau client", "nouveau dossier", "prêt pour M./Mme X"
   - CAS IMPORTANT : Le courtier envoie une LISTE/CHECKLIST de documents à fournir pour initialiser un nouveau dossier
     * Pièce jointe = liste de documents (ex: "Documents à fournir.pdf", "Checklist.pdf", "Liste des pièces.pdf")
     * Texte mentionne "documents dont nous aurons besoin", "liste des documents", "documents à fournir", "documents nécessaires"
     * Le courtier présente le dossier au client pour la première fois
     * Le courtier explique quels documents seront nécessaires pour monter le dossier
   - Tu dois extraire : nom, prénom, email du client, type de prêt, pièces mentionnées

2. ENVOI_DOCUMENTS : Le client (ou courtier) envoie des documents RÉELS pour un dossier existant
   - Indices : pièces jointes avec documents réels (CNI, bulletins, avis, images, etc.), "ci-joint", "voici les documents", "voici ce que vous m'avez demandé"
   - DIFFÉRENCE avec NOUVEAU_DOSSIER : Les pièces jointes sont des documents réels (CNI, bulletins de salaire, avis d'imposition, images, etc.), pas une liste/checklist
   - Noms de fichiers typiques : "CNI_recto_verso.pdf", "Bulletin_salaire_janvier.pdf", "Avis_imposition_2024.pdf", "WhatsApp Image...", photos, scans
   - CAS IMPORTANT : Email forwardé avec réponse du client
     * Si l'email est forwardé (Fwd:) et contient une réponse du client avec pièce jointe → ENVOI_DOCUMENTS
     * Ignore le contexte forwardé (conversation précédente), concentre-toi sur le NOUVEAU contenu
     * Si le client répond "voici", "ci-joint", "j'envoie" avec une pièce jointe → ENVOI_DOCUMENTS
   - Tu dois extraire : nombre de pièces, nom/prénom client si mentionné

3. MODIFIER_LISTE : Le courtier demande d'ajouter/retirer des pièces à la liste attendue
   - Indices : "il faut aussi", "ajouter", "finalement", "en plus", "retirer", "pas besoin de"
   - Tu dois extraire : nom client, pièces à ajouter, pièces à retirer

4. QUESTION : Le courtier pose une question ou demande une information
   - Indices : "?", "est-ce que", "peux-tu", "pourrais-tu"
   - Tu dois extraire : sujet de la question, urgence (bool)

5. CONTEXTE : Information contextuelle à conserver (remerciements, remarques, suivi)
   - Indices : "merci", "bien reçu", "à noter", "pour info"
   - Tu dois extraire : catégorie (remerciement/remarque/suivi)

RÈGLES DE DISTINCTION IMPORTANTES :

NOUVEAU_DOSSIER vs ENVOI_DOCUMENTS :
- NOUVEAU_DOSSIER : Le courtier envoie une LISTE/CHECKLIST de documents à fournir (document PDF listant les pièces nécessaires)
  * Exemples de noms de fichiers : "Documents à fournir.pdf", "Checklist.pdf", "Liste des pièces.pdf"
  * Le texte mentionne "liste des documents", "documents dont nous aurons besoin", "documents nécessaires"
  * Le courtier présente ce qui sera nécessaire pour monter le dossier
  
- ENVOI_DOCUMENTS : Le client envoie les documents RÉELS (CNI, bulletins, etc.) pour compléter un dossier existant
  * Exemples de noms de fichiers : "CNI.pdf", "Bulletin_salaire.pdf", "Avis_imposition.pdf"
  * Les pièces jointes sont des documents justificatifs réels, pas une liste

Si le courtier envoie une phrase qui signifie "la liste des documents nécessaires" avec une pièce jointe qui est une liste/checklist → NOUVEAU_DOSSIER
Si le client envoie des documents réels (CNI, bulletins, etc.) → ENVOI_DOCUMENTS

Réponds UNIQUEMENT avec un objet JSON valide suivant ce format exact :
{
  "action": "NOUVEAU_DOSSIER" | "ENVOI_DOCUMENTS" | "MODIFIER_LISTE" | "QUESTION" | "CONTEXTE",
  "resume": "Résumé en une phrase (max 200 caractères)",
  "confiance": 0.95,
  "details": {
    // Champs spécifiques selon l'action (voir exemples ci-dessous)
  }
}

EXEMPLES details selon action :

NOUVEAU_DOSSIER:
{
  "client_nom": "Dupont",
  "client_prenom": "Jean",
  "client_email": "jean.dupont@email.com",
  "type_pret": "immobilier",
  "pieces_mentionnees": ["carte identité", "bulletins salaire", "avis imposition"]
}

ENVOI_DOCUMENTS:
{
  "nombre_pieces": 3,
  "client_nom": "Martin",
  "client_prenom": "Sophie"
}

MODIFIER_LISTE:
{
  "client_nom": "Durand",
  "pieces_a_ajouter": ["compromis de vente", "6 relevés bancaires"],
  "pieces_a_retirer": []
}

QUESTION:
{
  "sujet": "Délai traitement dossier",
  "urgent": false
}

CONTEXTE:
{
  "categorie": "remerciement"
}

GESTION DES EMAILS FORWARDÉS (Fwd:) :

⚠️ ATTENTION : Si l'email est forwardé (sujet commence par "Fwd:" ou contient "---------- Forwarded message ---------") :

1. UTILISE le contexte forwardé pour COMPRENDRE la situation :
   - Identifie le client mentionné dans l'historique (nom, prénom, email)
   - Identifie le type de prêt (immobilier/professionnel) mentionné dans l'historique
   - Comprend la situation du dossier (nouveau dossier, dossier existant)
   - Extrait toutes les informations utiles du contexte historique

2. MAIS classe selon le NOUVEAU contenu (la réponse actuelle) :
   - Si le nouveau contenu est une réponse du client avec pièce jointe → ENVOI_DOCUMENTS
   - Si le nouveau contenu est une nouvelle demande du courtier → NOUVEAU_DOSSIER
   - Le contexte forwardé enrichit les détails (client_nom, type_pret, etc.), mais l'action est déterminée par le nouveau contenu

Exemple :
- Email forwardé avec contexte "liste des documents nécessaires pour M. Martin, prêt immobilier" + nouveau contenu "voici ce que vous m'avez demandé" + image
  → Action: ENVOI_DOCUMENTS (le client répond avec un document)
  → Détails: Utilise le contexte pour extraire client_nom="Martin", type_pret="immobilier"

- Email forwardé avec nouveau contenu "liste des documents nécessaires" + PDF liste
  → Action: NOUVEAU_DOSSIER (nouvelle demande du courtier)

IMPORTANT :
- Sois précis dans l'extraction des noms/prénoms
- Si information manquante, mets null
- La confiance doit refléter ta certitude (0.0 à 1.0)
- Le résumé doit être court et informatif
- Distingue bien LISTE de documents (NOUVEAU_DOSSIER) vs DOCUMENTS réels (ENVOI_DOCUMENTS)
- Analyse le nom du fichier joint : si c'est une liste/checklist → NOUVEAU_DOSSIER, si ce sont des documents réels → ENVOI_DOCUMENTS
- Pour les emails forwardés : utilise l'historique pour extraire les informations (client, type prêt), mais classe selon le nouveau contenu"""

    def _build_classification_prompt(
        self,
        email: EmailData,
        courtier: Dict,
        client_exists: bool = False
    ) -> str:
        """
        Construit le prompt utilisateur avec contexte email.

        Args:
            email: Email à classifier.
            courtier: Informations du courtier.
            client_exists: True si le client existe déjà en base de données.

        Returns:
            Prompt formaté pour Mistral.
        """
        # Construire info sur pièces jointes
        attachments_info = ""
        if email.attachments:
            attachments_info = f"\n\nPIÈCES JOINTES ({len(email.attachments)}) :\n"
            for att in email.attachments:
                attachments_info += f"- {att.filename} ({att.content_type}, {att.size_bytes} bytes)\n"

        # Corps du message (text ou html)
        body = email.body_text or email.body_html or "(vide)"

        # Détecter si c'est un email forwardé
        is_forwarded = email.subject.lower().startswith("fwd:") or "forwarded message" in body.lower() or "---------- Forwarded message ---------" in body
        
        # Contexte client
        client_context = ""
        if not client_exists:
            client_context = "\n⚠️ IMPORTANT : Le client n'existe pas encore en base de données. Si le courtier envoie une liste de documents à fournir, c'est probablement un NOUVEAU_DOSSIER."

        # Contexte email forwardé
        forwarded_context = ""
        if is_forwarded:
            forwarded_context = """
⚠️ EMAIL FORWARDÉ DÉTECTÉ :
- Cet email contient un historique forwardé (conversation précédente)
- UTILISE l'historique pour comprendre la situation et extraire les informations :
  * Nom, prénom, email du client mentionné dans l'historique
  * Type de prêt (immobilier/professionnel) mentionné dans l'historique
  * Contexte du dossier
- MAIS classe selon le NOUVEAU contenu (la réponse actuelle), pas l'historique :
  * Si le nouveau contenu est une réponse du client avec pièce jointe → ENVOI_DOCUMENTS
  * Si le nouveau contenu est une nouvelle demande du courtier → NOUVEAU_DOSSIER
- L'historique enrichit les détails, le nouveau contenu détermine l'action"""

        prompt = f"""Analyse cet email et détermine l'action à effectuer.

CONTEXTE :
- Courtier expéditeur : {courtier.get('prenom')} {courtier.get('nom')} ({courtier.get('email')})
{client_context}{forwarded_context}

EMAIL À ANALYSER :
De : {email.from_address}
Sujet : {email.subject}
{"⚠️ EMAIL FORWARDÉ" if is_forwarded else ""}

Corps du message :
{body}
{attachments_info}

{"⚠️ RAPPEL : Concentre-toi sur le NOUVEAU contenu, ignore le contexte forwardé" if is_forwarded else ""}

Réponds avec le JSON de classification."""

        return prompt

    async def extract_pieces_from_text(
        self,
        text: str
    ) -> List[Dict]:
        """
        Extrait et structure une liste de pièces depuis un texte libre.

        Utilisé quand le courtier demande d'ajouter des pièces.

        Args:
            text: Texte contenant la liste de pièces.

        Returns:
            Liste de dicts avec structure pièce.
        """
        logger.info("Extraction de pièces depuis texte via Mistral")

        prompt = f"""Extrait la liste des pièces/documents mentionnés dans ce texte :

"{text}"

Réponds avec un JSON array de cette forme :
{{
  "pieces": [
    {{
      "nom_piece": "Carte nationale d'identité",
      "categorie": "identite",
      "obligatoire": true
    }},
    {{
      "nom_piece": "3 derniers bulletins de salaire",
      "categorie": "revenus",
      "obligatoire": true
    }}
  ]
}}

Catégories possibles : identite, domicile, revenus, bancaire, projet, autre

Si pas sûr du caractère obligatoire, mets true par défaut.
Normalise les noms de pièces (ex: "CNI" → "Carte nationale d'identité")."""

        try:
            response = await self.client.chat.complete_async(
                model=self.model_chat,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            result = json.loads(response.choices[0].message.content)
            pieces = result.get("pieces", [])

            logger.info(f"Extraction réussie: {len(pieces)} pièce(s) identifiée(s)")
            return pieces

        except Exception as e:
            logger.error(f"Erreur extraction pièces via Mistral: {e}")
            return []

    def _get_fallback_classification(
        self,
        email: EmailData
    ) -> EmailClassification:
        """
        Retourne une classification par défaut en cas d'erreur Mistral.

        Args:
            email: Email à classifier.

        Returns:
            Classification QUESTION par défaut avec faible confiance.
        """
        logger.warning("Utilisation de la classification fallback")

        # Déterminer l'action par heuristique simple
        action = EmailAction.QUESTION
        details = {"sujet": "Classification automatique échouée", "urgent": False}

        # Si pièces jointes, probablement envoi documents
        if email.attachments and len(email.attachments) > 0:
            action = EmailAction.ENVOI_DOCUMENTS
            details = {"nombre_pieces": len(email.attachments)}

        return EmailClassification(
            action=action,
            resume=f"Classification fallback: {email.subject[:100]}",
            confiance=0.3,  # Faible confiance
            details=details
        )
