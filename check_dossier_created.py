#!/usr/bin/env python3
"""Vérifier si les dossiers ont été créés sur Drive"""

import logging
from app.services.drive import DriveManager
from app.utils.db import get_courtier_by_email

logging.basicConfig(level=logging.INFO)

drive = DriveManager()
courtier = get_courtier_by_email('beamkx@gmail.com')

print(f"Courtier: {courtier.get('prenom')} {courtier.get('nom')}")
print(f"Dossier courtier (DB): {courtier.get('dossier_drive_id')}")

# Essayer de lister les dossiers dans le dossier maître
try:
    master_folder_id = drive.master_folder_id
    print(f"\nDossier maître: {master_folder_id}")
    
    # Chercher les dossiers courtiers
    folders = drive.list_files_in_folder(master_folder_id, mime_type='application/vnd.google-apps.folder')
    print(f"\nDossiers dans le dossier maître: {len(folders)}")
    for folder in folders[:10]:
        print(f"  - {folder.get('name')} (ID: {folder.get('id')})")
    
    # Chercher un dossier courtier pour ce courtier
    courtier_folder_name = f"Courtier_{courtier.get('prenom')}_{courtier.get('nom')}"
    print(f"\nRecherche du dossier: {courtier_folder_name}")
    courtier_folders = [f for f in folders if courtier_folder_name in f.get('name', '')]
    
    if courtier_folders:
        courtier_folder_id = courtier_folders[0].get('id')
        print(f"✅ Dossier courtier trouvé: {courtier_folder_id}")
        
        # Chercher les dossiers clients
        client_folders = drive.list_files_in_folder(courtier_folder_id, mime_type='application/vnd.google-apps.folder')
        print(f"\nDossiers clients trouvés: {len(client_folders)}")
        for folder in client_folders:
            print(f"  - {folder.get('name')} (ID: {folder.get('id')})")
    else:
        print(f"❌ Dossier courtier non trouvé")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

