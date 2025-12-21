"""
Test simple pour voir la classification des emails avec pièces jointes.
"""
import asyncio
import sys
from app.services.email_fetcher import EmailFetcher
from app.services.email_parser import EmailParser

async def main():
    print("🔍 Récupération et classification des emails...")
    print("=" * 80)

    # Récupérer les emails
    fetcher = EmailFetcher()
    try:
        if not fetcher.connect():
            print("❌ Impossible de se connecter à IMAP")
            return

        emails = fetcher.fetch_new_emails()
        print(f"\n📧 {len(emails)} email(s) récupéré(s)\n")

        for i, email in enumerate(emails, 1):
            print(f"\n{'='*80}")
            print(f"EMAIL #{i}")
            print(f"{'='*80}")
            print(f"De: {email.from_name or 'Inconnu'} <{email.from_address}>")
            print(f"Sujet: {email.subject[:60]}...")
            print(f"Pièces jointes: {len(email.attachments)}")

            if email.attachments:
                for att in email.attachments:
                    print(f"  📎 {att.filename} ({att.size_bytes} bytes)")

            # Identifier courtier
            courtier = EmailParser.identify_courtier(email)

            if not courtier:
                print(f"⚠️  Courtier non identifié - SKIP\n")
                continue

            print(f"✅ Courtier: {courtier.get('prenom')} {courtier.get('nom')}")

            # Identifier client
            client = EmailParser.identify_client(email, courtier.get('id'))
            client_exists = client is not None

            if client:
                print(f"✅ Client existant: {client.get('prenom')} {client.get('nom')}")
            else:
                print(f"🆕 Nouveau client")

            # Classification Mistral
            print(f"\n🤖 Classification Mistral...")
            classification = await EmailParser.classify_with_mistral(
                email,
                courtier,
                client
            )

            print(f"\n📋 RÉSULTAT CLASSIFICATION:")
            print(f"   🎯 Action: {classification.action.value}")
            print(f"   📊 Confiance: {classification.confiance:.0%}")
            print(f"   📝 Résumé: {classification.resume}")

            # Afficher les détails importants
            if classification.details:
                details = classification.details
                if 'client_nom' in details:
                    print(f"   👤 Client: {details.get('client_prenom', '')} {details.get('client_nom', '')}")
                if 'type_pret' in details:
                    print(f"   💰 Type prêt: {details.get('type_pret')}")
                if 'nombre_pieces' in details:
                    print(f"   📎 Nombre de pièces: {details.get('nombre_pieces')}")
                if 'types_detectes' in details:
                    types = details.get('types_detectes', [])
                    if types:
                        print(f"   📄 Types détectés: {', '.join(types)}")

    finally:
        fetcher.disconnect()

    print("\n" + "="*80)
    print("✅ Test terminé!")

if __name__ == "__main__":
    asyncio.run(main())
