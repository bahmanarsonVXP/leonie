"""
Test pour vérifier que les pièces jointes sont correctement traitées.
"""
import base64
from datetime import datetime
from pathlib import Path

from app.models.email import EmailData, EmailAttachment
from app.services.router import EmailRouter
from app.models.email import EmailClassification, EmailAction
from app.utils.db import get_courtier_by_email

# 1. Créer une pièce jointe de test
print("📄 Création d'une pièce jointe de test...")
test_content = b"Contenu PDF de test pour le justificatif de domicile"

attachment = EmailAttachment(
    filename="Justificatif_domicile.pdf",
    content_type="application/pdf",
    size_bytes=len(test_content),
    content=test_content
)

# 2. Créer un email de test
email = EmailData(
    message_id="<test-piece-jointe@gmail.com>",
    from_address="beamkx@gmail.com",
    from_name="BEAMKX Test",
    to_addresses=["leonie@voxperience.com"],
    cc_addresses=[],
    subject="Envoi justificatif de domicile pour Jean Dubois",
    body_text="Bonjour, voici le justificatif de domicile pour le dossier de Jean Dubois.",
    date=datetime.now(),
    attachments=[attachment]
)

# 3. Classification de test
classification = EmailClassification(
    action=EmailAction.ENVOI_DOCUMENTS,
    resume="Envoi justificatif domicile pour Jean Dubois",
    confiance=0.95,
    details={
        "client_nom": "Dubois",
        "client_prenom": "Jean",
        "nombre_pieces": 1,
        "types_detectes": ["justificatif domicile"]
    }
)

# 4. Récupérer le courtier
courtier = get_courtier_by_email("beamkx@gmail.com")
if not courtier:
    print("❌ Courtier BEAMKX non trouvé!")
    exit(1)

print(f"✅ Courtier trouvé: {courtier.get('prenom')} {courtier.get('nom')}")

# 5. Router l'email
print("\n📤 Envoi du job...")
import asyncio
result = asyncio.run(EmailRouter.route(email, classification, courtier))

print(f"\n✅ Job enqueued: {result.get('job_id')}")
print(f"   Action: {result.get('action')}")
print(f"   Status: {result.get('status')}")

# 6. Attendre et vérifier les logs
print("\n👀 Surveillez les logs du worker:")
print("   tail -f /tmp/worker_fixed.log")
print("\nLe job devrait traiter le fichier et l'uploader sur Drive.")
