#!/usr/bin/env python3
"""Test direct du job pour voir l'erreur"""

import logging
import sys
from app.workers.jobs import process_nouveau_dossier
from app.utils.db import get_courtier_by_email

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# Récupérer le courtier
courtier = get_courtier_by_email('beamkx@gmail.com')
courtier_id = str(courtier.get('id'))

# Données de test (comme celles du dernier email)
email_data = {
    'subject': 'Créer un dossier pour Jean Dubois ROI',
    'from_address': 'beamkx@gmail.com',
}

classification = {
    'details': {
        'client_nom': 'DuboisRoi',
        'client_prenom': 'Jean',
        'client_email': None,
        'type_pret': 'professionnel',
        'pieces_mentionnees': ['CNI', 'avis d\'imposition']
    }
}

print(f"Test du job process_nouveau_dossier")
print(f"Courtier ID: {courtier_id}")
print(f"Client: {classification['details']['client_prenom']} {classification['details']['client_nom']}")

try:
    result = process_nouveau_dossier(courtier_id, email_data, classification)
    print(f"\n✅ Succès!")
    print(f"Résultat: {result}")
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

