#!/usr/bin/env python3
"""Test direct du job pour René QuiSait"""

from app.workers.jobs import process_nouveau_dossier
from app.utils.db import get_courtier_by_email
from uuid import UUID

courtier = get_courtier_by_email('beamkx@gmail.com')
courtier_id = str(courtier.get('id'))

email_data = {
    'subject': 'Créer un dossier pour René QuiSait',
    'from_address': 'beamkx@gmail.com',
}

classification = {
    'action': 'NOUVEAU_DOSSIER',
    'details': {
        'client_nom': 'QuiSait',
        'client_prenom': 'René',
        'client_email': None,
        'type_pret': 'professionnel',
        'pieces_mentionnees': ['CNI', 'Kbis']
    }
}

print(f"Test du job pour: René QuiSait")
print(f"Courtier ID: {courtier_id}")
print("=" * 80)

try:
    result = process_nouveau_dossier(courtier_id, email_data, classification)
    print("\n✅ Succès!")
    print(f"   client_folder_id: {result.get('client_folder_id')}")
    print(f"   courtier_folder_id: {result.get('courtier_folder_id')}")
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

