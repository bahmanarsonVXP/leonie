#!/usr/bin/env python3
"""Vérifier si le nouveau dossier a été créé"""

from app.services.drive import DriveManager
from app.utils.db import get_courtier_by_email

drive = DriveManager()
courtier = get_courtier_by_email('beamkx@gmail.com')

# Le dossier courtier actuel dans la DB
courtier_folder_id_db = courtier.get('dossier_drive_id')
print(f"Dossier courtier (DB): {courtier_folder_id_db}")

# Chercher tous les dossiers clients possibles
possible_names = [
    "CLIENT_QuiSait_René",
    "CLIENT_QuiSait_Rene", 
    "CLIENT_QuiSait_Rene",
]

try:
    # Lister le contenu du dossier courtier
    files = drive.list_files_in_folder(courtier_folder_id_db, mime_type='application/vnd.google-apps.folder')
    print(f"\nDossiers clients dans le dossier courtier: {len(files)}")
    for folder in files:
        name = folder.get('name', '')
        print(f"  - {name} (ID: {folder.get('id')})")
        
        # Si c'est le nouveau dossier
        if "QuiSait" in name or "René" in name or "Rene" in name:
            print(f"    ✅ NOUVEAU DOSSIER TROUVÉ!")
except Exception as e:
    print(f"\n❌ Erreur: {e}")

