"""
Test du scénario: Courtier forward un email client avec pièces jointes.

Scénario:
1. Client envoie email avec pièces au courtier
2. Courtier forward à Léonie

Que va faire Léonie?
"""
import asyncio
from datetime import datetime
from app.models.email import EmailData, EmailAttachment, EmailClassification
from app.services.email_parser import EmailParser
from app.utils.db import get_courtier_by_email

async def test_scenario():
    print("🧪 TEST: Email forwardé par courtier avec pièces jointes")
    print("=" * 80)

    # Simuler l'email forwardé
    # L'expéditeur est le courtier (qui a fait le forward)
    # Mais le contenu original vient du client

    email_content = """
---------- Forwarded message ---------
De: Jean Dupont <jean.dupont@gmail.com>
Date: sam. 21 déc. 2024 à 10:30
Sujet: Documents pour mon dossier
À: BeamKX <beamkx@gmail.com>

Bonjour,

Comme convenu lors de notre appel téléphonique, vous trouverez en pièce jointe
mon justificatif de domicile et ma carte d'identité.

Cordialement,
Jean Dupont
"""

    # Créer une pièce jointe simulée
    attachment = EmailAttachment(
        filename="CNI_Jean_Dupont.pdf",
        content_type="application/pdf",
        size_bytes=1500000,  # 1.5 MB
        content=b"PDF content here..."
    )

    # L'email tel que Léonie va le recevoir
    email = EmailData(
        message_id="<forwarded-test@gmail.com>",
        from_address="beamkx@gmail.com",  # ⚠️ Expéditeur = courtier (qui forward)
        from_name="BeamKX",
        to_addresses=["leonie@voxperience.com"],
        cc_addresses=[],
        subject="Fwd: Documents pour mon dossier",  # "Fwd:" indique un forward
        body_text=email_content,
        date=datetime.now(),
        attachments=[attachment]
    )

    print("\n📧 EMAIL REÇU:")
    print(f"   De: {email.from_address}")
    print(f"   Sujet: {email.subject}")
    print(f"   Pièces jointes: {len(email.attachments)}")
    print(f"   Contient 'Forwarded message': {'Oui' if 'Forwarded message' in email.body_text else 'Non'}")

    # Étape 1: Identifier le courtier
    print("\n" + "="*80)
    print("ÉTAPE 1: IDENTIFICATION COURTIER")
    print("="*80)

    courtier = EmailParser.identify_courtier(email)

    if courtier:
        print(f"✅ Courtier identifié: {courtier.get('prenom')} {courtier.get('nom')}")
        print(f"   Email: {courtier.get('email')}")
        print(f"   ID: {courtier.get('id')}")
    else:
        print("❌ Courtier non identifié")
        return

    # Étape 2: Identifier le client
    print("\n" + "="*80)
    print("ÉTAPE 2: IDENTIFICATION CLIENT")
    print("="*80)

    client = EmailParser.identify_client(email, courtier.get('id'))

    if client:
        print(f"✅ Client identifié en base: {client.get('prenom')} {client.get('nom')}")
        print(f"   Email: {client.get('email_principal')}")
    else:
        print(f"⚠️  Aucun client trouvé en base")
        print(f"   Recherche par from_address: {email.from_address} → C'est le courtier!")
        print(f"   Recherche par TO/CC: {email.to_addresses + email.cc_addresses}")
        print(f"\n   💡 PROBLÈME: L'email original du client (jean.dupont@gmail.com)")
        print(f"      est dans le CORPS de l'email, pas dans les headers!")

    # Étape 3: Classification Mistral
    print("\n" + "="*80)
    print("ÉTAPE 3: CLASSIFICATION MISTRAL")
    print("="*80)

    classification = await EmailParser.classify_with_mistral(
        email,
        courtier,
        client
    )

    print(f"\n📋 RÉSULTAT:")
    print(f"   Action: {classification.action.value}")
    print(f"   Confiance: {classification.confiance:.0%}")
    print(f"   Résumé: {classification.resume}")

    if classification.details:
        print(f"\n📝 Détails extraits par Mistral:")
        for key, value in classification.details.items():
            if isinstance(value, list) and len(value) > 3:
                print(f"   - {key}: {', '.join(str(v) for v in value[:3])}... ({len(value)} total)")
            else:
                print(f"   - {key}: {value}")

    # Étape 4: Que va-t-il se passer?
    print("\n" + "="*80)
    print("ÉTAPE 4: QUE VA FAIRE LÉONIE?")
    print("="*80)

    if classification.action.value == "ENVOI_DOCUMENTS":
        print("\n✅ Action détectée: ENVOI_DOCUMENTS")
        print("\n⚠️  COMPORTEMENT ACTUEL (Session 6):")
        print("   1. Job enqueued dans la queue 'default'")
        print("   2. Dans process_envoi_documents():")
        print("      - from_email = None (champ non défini)")
        print("      - Client non identifié (l'expéditeur est le courtier)")
        print("      - client_folder_id = master_folder_id (placeholder)")
        print("      - Les pièces sont uploadées dans le DOSSIER PRINCIPAL")
        print("      - ❌ PAS dans le dossier du client Jean Dupont")
        print("\n💡 AMÉLIORATION NÉCESSAIRE (Session 7):")
        print("   1. Détecter qu'il s'agit d'un forward")
        print("   2. Parser le contenu pour extraire l'email original")
        print("   3. Utiliser Mistral pour identifier le client par son nom")
        print("   4. Chercher le dossier client ou demander confirmation au courtier")

    elif classification.action.value == "NOUVEAU_DOSSIER":
        print("\n⚠️  Action détectée: NOUVEAU_DOSSIER")
        print("   Mistral pense qu'il faut créer un nouveau dossier")
        print("   Mais c'est probablement un dossier existant!")

    print("\n" + "="*80)
    print("✅ Test terminé")
    print("="*80)

asyncio.run(test_scenario())
