#!/usr/bin/env python3
"""
Script pour tester la classification Mistral sur le dernier email de beamkx@gmail.com
"""

import asyncio
import logging
from app.services.email_fetcher import EmailFetcher
from app.services.email_parser import EmailParser
from app.models.email import EmailData

# Configuration du logging pour voir les détails
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_email_beamkx():
    """Récupère et teste la classification du dernier email de beamkx@gmail.com"""
    
    print("=" * 80)
    print("TEST DE CLASSIFICATION MISTRAL - Email de beamkx@gmail.com")
    print("=" * 80)
    
    # 1. Récupérer tous les emails récents
    print("\n1. Récupération des emails via IMAP...")
    with EmailFetcher() as fetcher:
        emails = fetcher.fetch_new_emails()
        print(f"   ✓ {len(emails)} email(s) récupéré(s)")
    
    # 2. Filtrer les emails de beamkx@gmail.com
    print("\n2. Recherche des emails de beamkx@gmail.com...")
    emails_beamkx = [
        email for email in emails 
        if email.from_address.lower() == "beamkx@gmail.com"
    ]
    
    if not emails_beamkx:
        print("   ✗ Aucun email trouvé de beamkx@gmail.com")
        print("\n   Emails trouvés (expéditeurs):")
        for email in emails[:5]:  # Afficher les 5 premiers
            print(f"   - {email.from_address}: {email.subject[:50]}")
        return
    
    # Trier par date (plus récent en premier)
    emails_beamkx.sort(key=lambda e: e.date, reverse=True)
    last_email = emails_beamkx[0]
    
    print(f"   ✓ {len(emails_beamkx)} email(s) trouvé(s) de beamkx@gmail.com")
    print(f"   ✓ Dernier email: {last_email.subject}")
    print(f"   ✓ Date: {last_email.date}")
    
    # 3. Afficher les détails de l'email
    print("\n" + "=" * 80)
    print("3. DÉTAILS DE L'EMAIL")
    print("=" * 80)
    print(f"Message ID: {last_email.message_id}")
    print(f"De: {last_email.from_address} ({last_email.from_name or 'N/A'})")
    print(f"À: {', '.join(last_email.to_addresses)}")
    if last_email.cc_addresses:
        print(f"CC: {', '.join(last_email.cc_addresses)}")
    print(f"Sujet: {last_email.subject}")
    print(f"Date: {last_email.date}")
    print(f"Pièces jointes: {len(last_email.attachments)}")
    if last_email.attachments:
        for att in last_email.attachments:
            print(f"  - {att.filename} ({att.content_type}, {att.size_bytes} bytes)")
    
    print(f"\nCorps du message (texte):")
    print("-" * 80)
    if last_email.body_text:
        print(last_email.body_text[:500] + ("..." if len(last_email.body_text) > 500 else ""))
    elif last_email.body_html:
        print("(HTML uniquement)")
    else:
        print("(vide)")
    print("-" * 80)
    
    # 4. Identifier le courtier
    print("\n" + "=" * 80)
    print("4. IDENTIFICATION DU COURTIER")
    print("=" * 80)
    courtier = EmailParser.identify_courtier(last_email)
    
    if courtier:
        print(f"✅ Courtier identifié:")
        print(f"   - Nom: {courtier.get('prenom')} {courtier.get('nom')}")
        print(f"   - Email: {courtier.get('email')}")
        print(f"   - ID: {courtier.get('id')}")
        print(f"   - Actif: {courtier.get('actif')}")
    else:
        print(f"❌ Aucun courtier trouvé pour l'email: {last_email.from_address}")
        print("\n   Pour que l'email soit traité, il faut créer un courtier dans Supabase:")
        print(f"   INSERT INTO courtiers (email, nom, prenom, dossier_drive_id, actif)")
        print(f"   VALUES ('{last_email.from_address}', 'Nom', 'Prénom', 'drive-id', true);")
        return
    
    # 5. Identification du client (pour contexte Mistral)
    print("\n" + "=" * 80)
    print("5. IDENTIFICATION DU CLIENT (pour contexte)")
    print("=" * 80)
    client = None
    if courtier:
        client = EmailParser.identify_client(last_email, courtier.get("id"))
        if client:
            print(f"✅ Client identifié: {client.get('prenom')} {client.get('nom')}")
        else:
            print(f"ℹ️  Client non identifié (nouveau dossier probable)")
    
    # 6. Classification Mistral
    print("\n" + "=" * 80)
    print("6. CLASSIFICATION MISTRAL AI")
    print("=" * 80)
    print("   Appel de l'API Mistral en cours...")
    
    try:
        classification = await EmailParser.classify_with_mistral(last_email, courtier, client)
        
        print(f"\n✅ Classification réussie!")
        print(f"\n📊 RÉSULTAT:")
        print(f"   Action détectée: {classification.action.value}")
        print(f"   Confiance: {classification.confiance:.2%}")
        print(f"   Résumé: {classification.resume}")
        
        print(f"\n📋 DÉTAILS EXTRITS:")
        import json
        print(json.dumps(classification.details, indent=2, ensure_ascii=False))
        
        print(f"\n📝 OBJET COMPLET:")
        print(json.dumps(classification.model_dump(), indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la classification: {e}")
        import traceback
        traceback.print_exc()
    
    # 7. Informations client extraites
    print("\n" + "=" * 80)
    print("7. INFORMATIONS CLIENT EXTRAITES")
    print("=" * 80)
    if courtier and not client:
        client_info = EmailParser.extract_client_info_from_email(last_email)
        if client_info:
            print(f"   Informations extraites: {client_info}")
        else:
            print(f"   Aucune information client extraite")

if __name__ == "__main__":
    asyncio.run(test_email_beamkx())

