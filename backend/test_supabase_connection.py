import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ajouter le répertoire parent au path pour importer app
sys.path.append(str(Path(__file__).parent))

try:
    from supabase import create_client
except ImportError:
    print("Erreur: Le package 'supabase' n'est pas installé.")
    print("Exécutez: pip install supabase python-dotenv")
    sys.exit(1)

def test_connection():
    # Charger les variables d'environnement
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    print("="*60)
    print("TEST DE CONNEXION SUPABASE")
    print("="*60)
    
    if not url or not key:
        print("❌ Erreur: SUPABASE_URL ou SUPABASE_KEY manquant dans .env")
        return
        
    print(f"URL: {url}")
    print(f"KEY: {key[:5]}...{key[-5:] if len(key) > 10 else ''}")
    if service_key:
        print(f"SERVICE_KEY: {service_key[:5]}...{service_key[-5:] if len(service_key) > 10 else ''}")
    else:
        print("SERVICE_KEY: Non trouvée (le test d'écriture utilisera la clé standard)")
    
    try:
        print("\nTentative de connexion...")
        
        # Test 1: Lecture simple avec clé normale (souvent anon)
        print("Test 1: Lecture table 'config' (Clé standard)...")
        supabase_anon = create_client(url, key)
        response = supabase_anon.table("config").select("*").limit(1).execute()
        print("✅ Lecture Config OK")
        
        # Sélection de la clé pour le test d'écriture
        key_for_write = service_key if service_key else key
        key_type = "SERVICE_ROLE_KEY" if service_key else "SUPABASE_KEY"
        
        print(f"\nTest 2: Test des permissions 'Service Role' (Écriture table 'clients')...")
        print(f"Utilisation de la clé: {key_type}")
        
        supabase_admin = create_client(url, key_for_write)
        
        try:
            # On tente d'insérer un client bidon pour voir si on a le droit
            # Utilisation d'un email improbable pour éviter les conflits
            dummy_email = "test_service_key_verify@leonie.local"
            
            # Vérifier s'il existe déjà et le supprimer si besoin (nettoyage)
            supabase_admin.table("clients").delete().eq("email_principal", dummy_email).execute()
            
            # Tentative d'insertion
            dummy_data = {
                "nom": "TEST_KEY",
                "email_principal": dummy_email,
                # courtier_id manquant va probablement déclencher une erreur FK ou NOT NULL, ce qui est bon signe (pas RLS)
            }
            
            # NOTE: Si courtier_id est NOT NULL, cela va échouer avec une erreur de contrainte
            # mais PAS une erreur RLS (42501). Une erreur de contrainte prouve qu'on a passé le RLS !
            
            print(f"Tentative insertion client test ({dummy_email})...")
            # Utilise le client admin explicitement
            supabase_admin.table("clients").insert(dummy_data).execute()
            
            print("✅ Écriture Clients OK (La clé est bien une clé Service/Admin !)")
            
            # Nettoyage
            supabase_admin.table("clients").delete().eq("email_principal", dummy_email).execute()
            print("✅ Nettoyage OK")
            
        except Exception as e:
            err_str = str(e)
            if "42501" in err_str or "violates row-level security" in err_str:
                print("\n❌ ÉCHEC TEST SERVICE ROLE")
                print("ERREUR RLS (42501) : Cette clé n'a pas les droits d'écriture (c'est une clé 'anon').")
                print(f"Clé utilisée (début): {key[:30]}...")
                print("Il faut utiliser la clé 'service_role' (starts with eyJ...) de la section Legacy keys.")
            elif "violates foreign key constraint" in err_str or "violates not-null constraint" in err_str:
                print("\n✅ Service Role Probable (Erreur de contrainte SQL = RLS passé !)")
                print(f"Détail: {err_str}")
            else:
                print(f"\n⚠️ Erreur inattendue lors de l'écriture: {err_str}")

    except Exception as e:
        print("\n❌ ÉCHEC DE LA CONNEXION GLOBALE")
        print(f"Erreur: {str(e)}")
        
        if "gwt" in str(e).lower() or "jwt" in str(e).lower() or "401" in str(e):
            print("\nConseil: Vérifiez que votre SUPABASE_KEY est valide et n'a pas expiré.")
        elif "refused" in str(e).lower():
            print("\nConseil: Vérifiez votre SUPABASE_URL (et l'accès internet).")

if __name__ == "__main__":
    test_connection()
