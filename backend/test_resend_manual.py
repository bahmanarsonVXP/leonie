import os
import resend
from dotenv import load_dotenv

# Charger les variables depuis .env
load_dotenv()

# Récupération de la clé depuis l'environnement
key = os.getenv("RESEND_API_KEY")

print("--- Test Manuel Resend ---")

if not key:
    print("❌ Erreur: Variable 'RESEND_API_KEY' introuvable.")
    print("Veuillez l'ajouter dans votre fichier .env :")
    print("RESEND_API_KEY=re_123456...")
    exit(1)

resend.api_key = key
print(f"🔑 Clé API détectée: {key[:5]}...{key[-5:]}")

try:
    print(f"📨 Tentative d'envoi de leonie@voxperience.com vers arsonbahman@gmail.com...")
    r = resend.Emails.send({
        "from": "leonie@voxperience.com",
        "to": "arsonbahman@gmail.com",
        "subject": "Test Resend - Custom Domain",
        "html": "<p>Test d'envoi avec domaine personnalisé.</p>"
    })
    
    if r and "id" in r:
        print(f"✅ SUCCÈS ! Email envoyé.")
        print(f"🆔 ID Resend: {r['id']}")
    else:
        print(f"⚠️ Réponse inattendue: {r}")

except Exception as e:
    print(f"❌ ÉCHECK de l'envoi : {e}")
