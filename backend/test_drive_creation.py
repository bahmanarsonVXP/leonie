#!/usr/bin/env python3
"""Test direct de création de dossier Drive"""

import logging
from app.services.drive import DriveManager
from app.utils.db import get_courtier_by_email

logging.basicConfig(level=logging.INFO)

# Récupérer le courtier
courtier = get_courtier_by_email('beamkx@gmail.com')
print(f"Courtier: {courtier.get('prenom')} {courtier.get('nom')}")
print(f"dossier_drive_id: {courtier.get('dossier_drive_id')}")

# Tester la création d'un dossier
drive = DriveManager()
courtier_folder_id = courtier.get('dossier_drive_id')
client_folder_name = "CLIENT_Dubois_Jean"

try:
    print(f"\nTentative de création du dossier '{client_folder_name}' dans '{courtier_folder_id}'...")
    client_folder_id = drive.get_or_create_folder(
        client_folder_name,
        courtier_folder_id
    )
    print(f"✅ Succès! Dossier créé avec ID: {client_folder_id}")
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

