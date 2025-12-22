"""
Script pour vérifier le contenu du dossier courtier sur Drive.
"""
from app.services.drive import DriveManager

drive = DriveManager()

# ID du dossier courtier (depuis les logs)
courtier_folder_id = "1iVVTO-teeHCON6IomGiH7fKZGC7xy8mo"

print(f"📁 Contenu du dossier courtier (ID: {courtier_folder_id}):")
print("=" * 70)

files = drive.list_files_in_folder(courtier_folder_id)

if files:
    for file in files:
        file_type = "📁" if file.get('mimeType') == 'application/vnd.google-apps.folder' else "📄"
        print(f"{file_type} {file.get('name')} (ID: {file.get('id')})")
else:
    print("(vide)")

print("=" * 70)
print(f"Total: {len(files)} élément(s)")
