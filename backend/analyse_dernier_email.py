#!/usr/bin/env python3
"""
Analyse le dernier email reçu par Léonie.
"""

import asyncio
import logging
from app.services.email_fetcher import EmailFetcher
from app.services.email_parser import EmailParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def analyser_dernier_email():
    """Récupère et analyse le dernier email reçu."""
    
    print("=" * 80)
    print("ANALYSE DU DERNIER EMAIL REÇU PAR LÉONIE")
    print("=" * 80)
    print()
    
    # 1. Récupérer les nouveaux emails
    print("1. Récupération des nouveaux emails via IMAP...")
    with EmailFetcher() as fetcher:
        emails = fetcher.fetch_new_emails()
        print(f"   ✓ {len(emails)} nouveau(x) email(s) récupéré(s)")
    
    if not emails:
        print("\n❌ Aucun nouvel email trouvé")
        return
    
    # Trier par date (plus récent en premier)
    emails.sort(key=lambda e: e.date, reverse=True)
    dernier_email = emails[0]
    
    print(f"\n📧 DERNIER EMAIL REÇU:")
    print(f"   Date: {dernier_email.date}")
    print(f"   De: {dernier_email.from_address} ({dernier_email.from_name or 'N/A'})")
    print(f"   Sujet: {dernier_email.subject}")
    print()
    
    # 2. Afficher les détails complets
    print("=" * 80)
    print("2. DÉTAILS DE L'EMAIL")
    print("=" * 80)
    print(f"Message ID: {dernier_email.message_id}")
    print(f"De: {dernier_email.from_address} ({dernier_email.from_name or 'N/A'})")
    print(f"À: {', '.join(dernier_email.to_addresses)}")
    if dernier_email.cc_addresses:
        print(f"CC: {', '.join(dernier_email.cc_addresses)}")
    print(f"Sujet: {dernier_email.subject}")
    print(f"Date: {dernier_email.date}")
    print(f"Pièces jointes: {len(dernier_email.attachments)}")
    if dernier_email.attachments:
        for att in dernier_email.attachments:
            print(f"  - {att.filename} ({att.content_type}, {att.size_bytes} bytes)")
    
    print(f"\nCorps du message:")
    print("-" * 80)
    if dernier_email.body_text:
        print(dernier_email.body_text[:500] + ("..." if len(dernier_email.body_text) > 500 else ""))
    elif dernier_email.body_html:
        print("(HTML uniquement)")
    else:
        print("(vide)")
    print("-" * 80)
    print()
    
    # 3. Identifier le courtier
    print("=" * 80)
    print("3. IDENTIFICATION DU COURTIER")
    print("=" * 80)
    courtier = EmailParser.identify_courtier(dernier_email)
    
    if not courtier:
        print(f"❌ Aucun courtier trouvé pour: {dernier_email.from_address}")
        print("\n   Cet email ne sera pas traité car l'expéditeur n'est pas un courtier enregistré.")
        return
    
    print(f"✅ Courtier identifié:")
    print(f"   - Nom: {courtier.get('prenom')} {courtier.get('nom')}")
    print(f"   - Email: {courtier.get('email')}")
    print(f"   - ID: {courtier.get('id')}")
    print()
    
    # 4. Identifier le client
    print("=" * 80)
    print("4. IDENTIFICATION DU CLIENT")
    print("=" * 80)
    client = EmailParser.identify_client(dernier_email, courtier.get("id"))
    
    if client:
        print(f"✅ Client identifié:")
        print(f"   - Nom: {client.get('prenom')} {client.get('nom')}")
        print(f"   - Email: {client.get('email_principal')}")
        print(f"   - ID: {client.get('id')}")
        client_exists = True
    else:
        print(f"ℹ️  Client non identifié (nouveau dossier probable)")
        client_info = EmailParser.extract_client_info_from_email(dernier_email)
        if client_info:
            print(f"   Informations extraites: {client_info}")
        client_exists = False
    print()
    
    # 5. Classification Mistral
    print("=" * 80)
    print("5. CLASSIFICATION MISTRAL AI")
    print("=" * 80)
    print("   Appel de l'API Mistral...")
    print()
    
    try:
        classification = await EmailParser.classify_with_mistral(dernier_email, courtier, client)
        
        print(f"✅ Classification réussie!")
        print()
        print(f"📊 ACTION DÉTECTÉE: {classification.action.value}")
        print(f"📈 Confiance: {classification.confiance:.0%}")
        print(f"📝 Résumé: {classification.resume}")
        print()
        print(f"📋 DÉTAILS EXTRITS:")
        import json
        print(json.dumps(classification.details, indent=2, ensure_ascii=False))
        print()
        
        # Analyse de la classification
        print("=" * 80)
        print("6. ANALYSE DE LA CLASSIFICATION")
        print("=" * 80)
        
        if classification.action.value == "NOUVEAU_DOSSIER":
            print("✅ Action: NOUVEAU_DOSSIER")
            print("   → Le courtier initie un nouveau dossier")
            if classification.details.get("client_nom"):
                print(f"   → Client: {classification.details.get('client_prenom', '')} {classification.details.get('client_nom', '')}")
            if classification.details.get("type_pret"):
                print(f"   → Type de prêt: {classification.details.get('type_pret')}")
        
        elif classification.action.value == "ENVOI_DOCUMENTS":
            print("✅ Action: ENVOI_DOCUMENTS")
            print("   → Le client envoie des documents pour un dossier existant")
            print(f"   → Nombre de pièces: {classification.details.get('nombre_pieces', 0)}")
        
        elif classification.action.value == "MODIFIER_LISTE":
            print("✅ Action: MODIFIER_LISTE")
            print("   → Le courtier modifie la liste des pièces attendues")
        
        elif classification.action.value == "QUESTION":
            print("✅ Action: QUESTION")
            print(f"   → Sujet: {classification.details.get('sujet', 'N/A')}")
            print(f"   → Urgent: {classification.details.get('urgent', False)}")
        
        elif classification.action.value == "CONTEXTE":
            print("✅ Action: CONTEXTE")
            print(f"   → Catégorie: {classification.details.get('categorie', 'N/A')}")
        
        print()
        print(f"💡 Contexte client: {'Existe en base' if client_exists else 'Nouveau client (indice pour NOUVEAU_DOSSIER)'}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la classification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyser_dernier_email())

