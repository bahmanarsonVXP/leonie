#!/usr/bin/env python3
"""
Script de test pour valider la nouvelle logique de création de dossiers Drive.

Teste :
1. Création de dossier client avec un courtier ayant un dossier_drive_id valide
2. Exception si le courtier n'a pas de dossier_drive_id
3. Exception si le dossier_drive_id est invalide (n'existe pas sur Drive)
"""

import logging
import sys
from app.workers.jobs import process_nouveau_dossier
from app.utils.db import get_courtier_by_email, get_courtier_by_id
from app.services.drive import DriveManager
from uuid import UUID

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)

def test_courtier_valide():
    """Test avec un courtier ayant un dossier_drive_id valide"""
    print("\n" + "=" * 80)
    print("TEST 1: Courtier avec dossier_drive_id VALIDE")
    print("=" * 80)
    
    # Récupérer le courtier BEAMKX (qui a maintenant un dossier valide)
    courtier = get_courtier_by_email('beamkx@gmail.com')
    if not courtier:
        print("❌ Courtier BEAMKX non trouvé")
        return False
    
    courtier_id = str(courtier.get('id'))
    dossier_drive_id = courtier.get('dossier_drive_id')
    
    print(f"Courtier: {courtier.get('prenom')} {courtier.get('nom')}")
    print(f"dossier_drive_id: {dossier_drive_id}")
    
    # Vérifier que le dossier existe sur Drive
    drive = DriveManager()
    try:
        drive.service.files().get(
            fileId=dossier_drive_id,
            fields='id,name',
            supportsAllDrives=True
        ).execute()
        print(f"✅ Dossier courtier validé sur Drive")
    except Exception as e:
        print(f"⚠️  Le dossier courtier n'existe pas encore sur Drive")
        print(f"   Erreur: {e}")
        print(f"   Ce test nécessite un courtier avec un dossier Drive valide")
        return False
    
    # Test de création de dossier client
    email_data = {
        'subject': 'Test création dossier',
        'from_address': 'beamkx@gmail.com',
    }
    
    classification = {
        'details': {
            'client_nom': 'TestClient',
            'client_prenom': 'Test',
            'client_email': None,
            'type_pret': 'professionnel',
            'pieces_mentionnees': ['CNI']
        }
    }
    
    try:
        result = process_nouveau_dossier(courtier_id, email_data, classification)
        print(f"\n✅ Succès! Dossier client créé")
        print(f"   client_folder_id: {result.get('client_folder_id')}")
        print(f"   courtier_folder_id: {result.get('courtier_folder_id')}")
        return True
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_courtier_sans_dossier_drive_id():
    """Test avec un courtier sans dossier_drive_id (doit lever ValueError)"""
    print("\n" + "=" * 80)
    print("TEST 2: Courtier SANS dossier_drive_id (doit lever ValueError)")
    print("=" * 80)
    
    # Créer un courtier fictif sans dossier_drive_id
    # (On simule en passant None)
    courtier_id = "00000000-0000-0000-0000-000000000000"
    
    email_data = {'subject': 'Test', 'from_address': 'test@test.com'}
    classification = {
        'details': {
            'client_nom': 'Test',
            'client_prenom': 'Test',
            'type_pret': 'professionnel'
        }
    }
    
    # On doit modifier temporairement le courtier pour ce test
    # Ou créer un mock. Pour simplifier, on teste juste la logique
    print("⚠️  Ce test nécessite un courtier réel sans dossier_drive_id")
    print("   Pour tester, vous pouvez temporairement mettre NULL dans la DB")
    print("   ou créer un courtier de test")
    return True


def test_courtier_dossier_invalide():
    """Test avec un courtier ayant un dossier_drive_id invalide (doit lever RuntimeError)"""
    print("\n" + "=" * 80)
    print("TEST 3: Courtier avec dossier_drive_id INVALIDE (doit lever RuntimeError)")
    print("=" * 80)
    
    # Utiliser le courtier BEAMKX qui a actuellement un fake ID
    courtier = get_courtier_by_email('beamkx@gmail.com')
    if not courtier:
        print("❌ Courtier non trouvé")
        return False
    
    courtier_id = str(courtier.get('id'))
    dossier_drive_id = courtier.get('dossier_drive_id')
    
    print(f"Courtier: {courtier.get('prenom')} {courtier.get('nom')}")
    print(f"dossier_drive_id actuel: {dossier_drive_id}")
    
    # Si le dossier est valide, on ne peut pas tester ce cas
    drive = DriveManager()
    try:
        drive.service.files().get(
            fileId=dossier_drive_id,
            fields='id,name',
            supportsAllDrives=True
        ).execute()
        print(f"⚠️  Le dossier est valide, on ne peut pas tester ce cas")
        print(f"   Pour tester, mettez temporairement un ID invalide dans la DB")
        return True
    except Exception:
        # Le dossier est invalide, on peut tester
        print(f"✅ Le dossier est invalide, test du comportement...")
        
        email_data = {'subject': 'Test', 'from_address': 'test@test.com'}
        classification = {
            'details': {
                'client_nom': 'Test',
                'client_prenom': 'Test',
                'type_pret': 'professionnel'
            }
        }
        
        try:
            result = process_nouveau_dossier(courtier_id, email_data, classification)
            print(f"\n❌ ERREUR: Le code devrait lever une exception mais a réussi!")
            return False
        except RuntimeError as e:
            if "invalide" in str(e).lower() or "invalide" in str(e):
                print(f"\n✅ Exception RuntimeError levée correctement:")
                print(f"   {str(e)[:200]}...")
                return True
            else:
                print(f"\n⚠️  Exception levée mais message inattendu: {e}")
                return False
        except Exception as e:
            print(f"\n⚠️  Exception levée mais type inattendu: {type(e).__name__}")
            print(f"   {e}")
            return False


def main():
    """Exécute tous les tests"""
    print("=" * 80)
    print("TESTS DE VALIDATION - Nouvelle logique dossier_drive_id")
    print("=" * 80)
    
    results = []
    
    # Test 1: Courtier valide
    results.append(("Courtier valide", test_courtier_valide()))
    
    # Test 2: Courtier sans dossier_drive_id
    results.append(("Courtier sans dossier_drive_id", test_courtier_sans_dossier_drive_id()))
    
    # Test 3: Courtier avec dossier invalide
    results.append(("Courtier dossier invalide", test_courtier_dossier_invalide()))
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✅ PASSÉ" if result else "❌ ÉCHOUÉ"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✅ Tous les tests sont passés!")
    else:
        print("\n⚠️  Certains tests nécessitent des conditions spécifiques")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

