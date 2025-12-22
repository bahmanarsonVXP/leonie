"""
Script pour ajouter un courtier dans Supabase.
"""

from supabase import create_client
from app.config import get_settings

settings = get_settings()

# Connexion Supabase
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Données du courtier
courtier_data = {
    "nom": "BEAM",
    "prenom": "KX",
    "email": "beamkx@gmail.com",
    "telephone": "+33600000000",  # Placeholder
    "entreprise": "Test Courtage"
}

print("🔧 Création du courtier BEAMKX...")
print(f"Email: {courtier_data['email']}")

try:
    # Vérifier si existe déjà
    result = supabase.table("courtiers").select("*").eq("email", courtier_data["email"]).execute()
    
    if result.data and len(result.data) > 0:
        print(f"\n✅ Courtier existe déjà!")
        print(f"ID: {result.data[0]['id']}")
        print(f"Nom: {result.data[0]['prenom']} {result.data[0]['nom']}")
    else:
        # Créer
        result = supabase.table("courtiers").insert(courtier_data).execute()
        print(f"\n✅ Courtier créé avec succès!")
        print(f"ID: {result.data[0]['id']}")
        print(f"Nom: {result.data[0]['prenom']} {result.data[0]['nom']}")
        print(f"Email: {result.data[0]['email']}")
        
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
