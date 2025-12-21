from app.services.drive import DriveManager

drive = DriveManager()

print("📁 Contenu du Shared Drive (DOSSIERS_PRETS):")
print("=" * 70)

files = drive.list_files_in_folder(drive.master_folder_id)

if files:
    for file in files:
        file_type = "📁" if file.get('mimeType') == 'application/vnd.google-apps.folder' else "📄"
        print(f"{file_type} {file.get('name')}")
else:
    print("(vide)")
    
print("=" * 70)
print(f"Total: {len(files)} élément(s)")
