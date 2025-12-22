from supabase import create_client
from app.config import get_settings

settings = get_settings()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

result = supabase.table("courtiers").select("*").eq("email", "beamkx@gmail.com").execute()

if result.data:
    courtier = result.data[0]
    print(f"✅ Courtier trouvé:")
    print(f"   ID: {courtier['id']}")
    print(f"   Nom: {courtier['prenom']} {courtier['nom']}")
    print(f"   Email: {courtier['email']}")
    print(f"   ⚠️  ACTIF: {courtier.get('actif', 'CHAMP MANQUANT')}")
else:
    print("❌ Courtier non trouvé")
