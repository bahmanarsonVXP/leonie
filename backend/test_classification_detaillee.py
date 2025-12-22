"""
Test détaillé pour voir la classification de chaque email.
"""
import asyncio
from app.cron.check_emails import check_new_emails
from app.services.email_fetcher import EmailFetcher
from app.services.email_parser import EmailParser
from app.config import get_settings

settings = get_settings()

async def test_classification():
    print("🔍 Récupération et analyse détaillée des emails...")
    print("=" * 80)

    # Récupérer les emails
    fetcher = EmailFetcher()
    emails = fetcher.fetch_new_emails(limit=10, mark_as_read=False)

    print(f"\n📧 {len(emails)} email(s) récupéré(s)\n")

    for i, email in enumerate(emails, 1):
        print(f"\n{'='*80}")
        print(f"EMAIL #{i}")
        print(f"{'='*80}")
        print(f"De: {email.from_name or 'Inconnu'} <{email.from_address}>")
        print(f"Sujet: {email.subject}")
        print(f"Date: {email.date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Pièces jointes: {len(email.attachments)}")

        if email.attachments:
            for att in email.attachments:
                print(f"  📎 {att.filename} ({att.size_bytes} bytes, {att.content_type})")

        # Identifier courtier
        courtier = EmailParser.identify_courtier(email)

        if not courtier:
            print(f"⚠️  Courtier non identifié - SKIP")
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

        print(f"\n📋 RÉSULTAT:")
        print(f"   Action: {classification.action.value}")
        print(f"   Confiance: {classification.confiance:.2%}")
        print(f"   Résumé: {classification.resume}")

        if classification.details:
            print(f"\n📝 Détails:")
            for key, value in classification.details.items():
                if key == 'pieces_mentionnees' and isinstance(value, list):
                    print(f"   - {key}: {len(value)} pièce(s)")
                elif isinstance(value, list):
                    print(f"   - {key}: {', '.join(str(v) for v in value[:3])}{'...' if len(value) > 3 else ''}")
                else:
                    print(f"   - {key}: {value}")

        print()

    print("\n" + "="*80)
    print("✅ Analyse terminée!")

asyncio.run(test_classification())
