"""
Vérifier que le fichier a bien été uploadé sur Google Drive.
"""
from app.services.drive import DriveManager

drive = DriveManager()

# ID du fichier uploadé (depuis les logs)
file_id = "1B8jb2DfdtfZJMHBmupf7wv4sioqQ396Y"

print(f"🔍 Vérification du fichier uploadé...")
print(f"   File ID: {file_id}")
print()

try:
    # Récupérer les métadonnées du fichier
    file_metadata = drive.service.files().get(
        fileId=file_id,
        fields="id, name, mimeType, size, createdTime, parents",
        supportsAllDrives=True
    ).execute()

    print("✅ Fichier trouvé sur Google Drive!")
    print(f"   Nom: {file_metadata.get('name')}")
    print(f"   Type: {file_metadata.get('mimeType')}")
    print(f"   Taille: {file_metadata.get('size')} bytes")
    print(f"   Créé: {file_metadata.get('createdTime')}")
    print(f"   Parent ID: {file_metadata.get('parents', ['Aucun'])[0]}")

    # Vérifier que c'est dans le master folder (placeholder actuel)
    parent_id = file_metadata.get('parents', [])[0] if file_metadata.get('parents') else None
    if parent_id == drive.master_folder_id:
        print(f"\n✅ Fichier correctement uploadé dans le dossier principal")
    else:
        print(f"\n⚠️  Fichier dans un autre dossier: {parent_id}")

except Exception as e:
    print(f"❌ Erreur: {e}")
