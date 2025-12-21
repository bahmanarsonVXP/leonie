"""
Script pour vérifier la structure complète d'un dossier client.
"""
from app.services.drive import DriveManager

drive = DriveManager()

# ID du dossier Jean Dubois (le premier créé)
client_folder_id = "1bg2_-4HssJCcNlbgVSidNcaTKRBZHIHM"

print(f"📁 Structure du dossier CLIENT_Dubois_Jean:")
print("=" * 70)

files = drive.list_files_in_folder(client_folder_id)

if files:
    folders = sorted([f for f in files if f.get('mimeType') == 'application/vnd.google-apps.folder'],
                     key=lambda x: x.get('name'))
    documents = [f for f in files if f.get('mimeType') != 'application/vnd.google-apps.folder']

    if folders:
        print("\n📂 DOSSIERS:")
        for folder in folders:
            print(f"   📁 {folder.get('name')}")

    if documents:
        print("\n📄 FICHIERS:")
        for doc in documents:
            print(f"   📄 {doc.get('name')}")

    print("\n" + "=" * 70)
    print(f"Total: {len(folders)} dossier(s), {len(documents)} fichier(s)")
else:
    print("(vide)")
