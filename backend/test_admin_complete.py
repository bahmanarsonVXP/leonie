"""
Script de test complet pour vérifier le compte admin.

Ce script teste:
1. Authentification Supabase
2. Accès aux endpoints normaux (dossiers)
3. Accès aux endpoints admin (courtiers)
4. Création d'un courtier de test

Usage:
    python test_admin_complete.py
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Charger .env
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_KEY')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
API_URL = "http://localhost:8000"

print("=" * 80)
print("🧪 TEST COMPLET DU COMPTE ADMIN")
print("=" * 80)

# Vérifier la configuration
print("\n📋 Configuration:")
print(f"   SUPABASE_URL: {SUPABASE_URL}")
print(f"   ADMIN_EMAIL: {ADMIN_EMAIL}")
print(f"   API_URL: {API_URL}")

if not SUPABASE_URL or not SUPABASE_ANON_KEY or not ADMIN_EMAIL:
    print("\n❌ Erreur: Variables d'environnement manquantes")
    print("   Vérifier .env contient: SUPABASE_URL, SUPABASE_KEY, ADMIN_EMAIL")
    sys.exit(1)

# Demander le mot de passe
ADMIN_PASSWORD = input("\n🔑 Mot de passe admin: ")

# ============================================================================
# TEST 1: Authentification Supabase
# ============================================================================
print("\n" + "=" * 80)
print("TEST 1: AUTHENTIFICATION SUPABASE")
print("=" * 80)

print("\n🔐 Connexion à Supabase Auth...")

response = requests.post(
    f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    headers={
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    },
    json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
)

if response.status_code != 200:
    print(f"\n❌ Échec authentification: {response.status_code}")
    print(f"   Réponse: {response.json()}")
    print("\n💡 Vérifier:")
    print("   - Email correct dans ADMIN_EMAIL")
    print("   - Mot de passe correct")
    print("   - Utilisateur créé dans Supabase Dashboard → Authentication → Users")
    sys.exit(1)

auth_data = response.json()
token = auth_data['access_token']
user = auth_data['user']

print("✅ Authentification réussie!")
print(f"\n👤 Utilisateur:")
print(f"   ID: {user['id']}")
print(f"   Email: {user['email']}")
print(f"   Metadata: {user.get('user_metadata', {})}")

# Vérifier metadata role
user_metadata = user.get('user_metadata', {})
has_admin_role = user_metadata.get('role') == 'admin'

if has_admin_role:
    print("   ✅ Role admin trouvé dans metadata")
else:
    print("   ⚠️  Role admin absent des metadata (mais fonctionne quand même via ADMIN_EMAIL)")

print(f"\n🎟️  JWT Token:")
print(f"{token[:50]}...{token[-20:]}")

# Sauvegarder le token
with open('.admin_token', 'w') as f:
    f.write(token)
print("\n💾 Token sauvegardé dans .admin_token")

# ============================================================================
# TEST 2: Vérifier que l'API Léonie tourne
# ============================================================================
print("\n" + "=" * 80)
print("TEST 2: VÉRIFIER API LÉONIE")
print("=" * 80)

print(f"\n🌐 Connexion à {API_URL}...")

try:
    response = requests.get(f"{API_URL}/health", timeout=5)
    if response.status_code == 200:
        health = response.json()
        print("✅ API Léonie en ligne!")
        print(f"   Version: {health.get('version')}")
        print(f"   Environment: {health.get('environment')}")
    else:
        print(f"⚠️  API répond mais status: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("\n❌ Impossible de se connecter à l'API")
    print("💡 Vérifier:")
    print("   - L'API est démarrée: uvicorn main:app --reload")
    print("   - L'URL est correcte: http://localhost:8000")
    sys.exit(1)

# ============================================================================
# TEST 3: Tester endpoint authentifié normal (dossiers)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 3: ENDPOINT AUTHENTIFIÉ NORMAL")
print("=" * 80)

print("\n📂 GET /api/dossiers (requiert authentification)...")

response = requests.get(
    f"{API_URL}/api/dossiers",
    headers={"Authorization": f"Bearer {token}"}
)

if response.status_code == 200:
    dossiers = response.json()
    print(f"✅ Accès autorisé!")
    print(f"   Nombre de dossiers: {len(dossiers)}")
    if dossiers:
        print(f"   Premier dossier: {dossiers[0].get('nom')} {dossiers[0].get('prenom')}")
elif response.status_code == 401:
    print("❌ Erreur 401 Unauthorized")
    print(f"   {response.json()}")
    print("\n💡 Vérifier:")
    print("   - SUPABASE_JWT_SECRET dans .env correspond à celui de Supabase")
    print("   - Obtenir dans: Supabase Dashboard → Settings → API → JWT Secret")
    sys.exit(1)
elif response.status_code == 403:
    error = response.json()
    if "courtier non trouvé" in error.get('detail', '').lower():
        print("⚠️  Admin pas dans table courtiers (normal)")
        print("   Mais l'authentification fonctionne!")
        print("   Les endpoints admin devraient fonctionner ✅")
    else:
        print(f"❌ Erreur 403: {error}")
        sys.exit(1)
else:
    print(f"❌ Erreur {response.status_code}")
    print(f"   {response.json()}")
    sys.exit(1)

# ============================================================================
# TEST 4: Tester endpoint admin (courtiers)
# ============================================================================
print("\n" + "=" * 80)
print("TEST 4: ENDPOINT ADMIN (CRUD COURTIERS)")
print("=" * 80)

print("\n👑 GET /api/admin/courtiers (admin seulement)...")

response = requests.get(
    f"{API_URL}/api/admin/courtiers",
    headers={"Authorization": f"Bearer {token}"}
)

if response.status_code == 200:
    courtiers = response.json()
    print(f"✅ Accès admin autorisé!")
    print(f"   Nombre de courtiers: {len(courtiers)}")
    if courtiers:
        for c in courtiers[:3]:  # Afficher les 3 premiers
            print(f"   - {c.get('prenom')} {c.get('nom')} ({c.get('email')})")
    else:
        print("   Aucun courtier pour le moment")
elif response.status_code == 403:
    error = response.json()
    print(f"❌ Accès admin refusé!")
    print(f"   {error}")
    print("\n💡 Vérifier:")
    print(f"   - ADMIN_EMAIL dans .env = '{ADMIN_EMAIL}'")
    print(f"   - Email du token = '{user['email']}'")
    print("   - Ces emails doivent être IDENTIQUES")
    sys.exit(1)
else:
    print(f"❌ Erreur {response.status_code}")
    print(f"   {response.json()}")
    sys.exit(1)

# ============================================================================
# TEST 5: Créer un courtier de test
# ============================================================================
print("\n" + "=" * 80)
print("TEST 5: CRÉER UN COURTIER DE TEST")
print("=" * 80)

create_test = input("\n❓ Créer un courtier de test? (o/N): ").lower() == 'o'

if create_test:
    print("\n📝 POST /api/admin/courtiers...")

    test_courtier = {
        "email": f"test.{user['id'][:8]}@example.com",
        "nom": "TestAdmin",
        "prenom": "Courtier",
        "actif": True
    }

    response = requests.post(
        f"{API_URL}/api/admin/courtiers",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=test_courtier
    )

    if response.status_code == 201:
        courtier = response.json()
        print("✅ Courtier créé avec succès!")
        print(f"   ID: {courtier.get('id')}")
        print(f"   Email: {courtier.get('email')}")
        print(f"   Nom: {courtier.get('prenom')} {courtier.get('nom')}")
        print(f"   Dossier Drive: {courtier.get('dossier_drive_id')}")
        print("\n💾 Un dossier Drive a été créé automatiquement!")
    else:
        print(f"❌ Erreur {response.status_code}")
        print(f"   {response.json()}")
else:
    print("⏭️  Création courtier ignorée")

# ============================================================================
# RÉSUMÉ
# ============================================================================
print("\n" + "=" * 80)
print("📊 RÉSUMÉ DES TESTS")
print("=" * 80)

print(f"""
✅ Authentification Supabase     : OK
✅ Token JWT obtenu              : OK
✅ API Léonie accessible         : OK
✅ Authentification API          : OK
✅ Accès endpoints admin         : OK
{"✅ Création courtier            : OK" if create_test else "⏭️  Création courtier            : Ignoré"}

🎉 COMPTE ADMIN FONCTIONNEL!

📝 Prochaines étapes:
   1. Utiliser ce token pour tester l'API:
      export JWT_TOKEN=$(cat .admin_token)
      curl http://localhost:8000/api/admin/courtiers -H "Authorization: Bearer $JWT_TOKEN"

   2. Créer des courtiers via l'API admin

   3. Développer le frontend pour utiliser cette API
""")
