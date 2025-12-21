#!/usr/bin/env python3
"""
Script pour tester l'accès à un dossier Drive spécifique
"""

import logging
from app.services.drive import DriveManager

logging.basicConfig(level=logging.INFO)

drive = DriveManager()
folder_id = "1iVVTO-teeHCON6IomGiH7fKZGC7xy8mo"

print(f"Test d'accès au dossier Drive: {folder_id}")
print("-" * 80)

# Test 1: Accès simple avec get()
print("\n1. Test avec files().get() (méthode actuelle)")
try:
    result = drive.service.files().get(
        fileId=folder_id,
        fields='id,name,mimeType,parents',
        supportsAllDrives=True
    ).execute()
    print(f"✅ Succès!")
    print(f"   ID: {result.get('id')}")
    print(f"   Nom: {result.get('name')}")
    print(f"   Type: {result.get('mimeType')}")
    print(f"   Parents: {result.get('parents', [])}")
except Exception as e:
    print(f"❌ Erreur: {e}")
    error_str = str(e)
    if "404" in error_str or "not found" in error_str.lower():
        print("\n   → Le dossier n'existe pas ou n'est pas accessible")
    elif "403" in error_str or "forbidden" in error_str.lower():
        print("\n   → Le dossier existe mais le Service Account n'a pas les permissions")
    elif "401" in error_str or "unauthorized" in error_str.lower():
        print("\n   → Problème d'authentification")
    else:
        print(f"\n   → Autre erreur: {type(e).__name__}")

# Test 2: Vérifier si c'est un Shared Drive
print("\n2. Test avec list() pour vérifier les permissions")
try:
    # Essayer de lister les fichiers dans ce dossier
    query = f"'{folder_id}' in parents and trashed=false"
    results = drive.service.files().list(
        q=query,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        pageSize=1
    ).execute()
    
    files = results.get('files', [])
    print(f"✅ Peut accéder au contenu du dossier")
    print(f"   Nombre de fichiers/dossiers: {len(files)}")
except Exception as e:
    print(f"❌ Erreur lors de la liste: {e}")
    error_str = str(e)
    if "403" in error_str or "forbidden" in error_str.lower():
        print("\n   → Le Service Account n'a pas les permissions pour lire ce dossier")
        print("   → Solution: Partager le dossier avec l'email du Service Account")
    elif "404" in error_str or "not found" in error_str.lower():
        print("\n   → Le dossier n'existe pas")

# Test 3: Vérifier les permissions du Service Account
print("\n3. Informations du Service Account")
try:
    # Obtenir l'email du Service Account
    settings = drive.service.about().get(fields="user").execute()
    print(f"✅ Service Account actif")
    # Note: Cette requête peut ne pas retourner l'email selon les permissions
except Exception as e:
    print(f"⚠️  Impossible d'obtenir les infos du Service Account: {e}")

print("\n" + "=" * 80)
print("RECOMMANDATIONS:")
print("=" * 80)
print("1. Si erreur 404: Le dossier n'existe pas → Vérifier l'ID dans Google Drive")
print("2. Si erreur 403: Le Service Account n'a pas accès → Partager le dossier avec")
print("   l'email du Service Account dans Google Drive")
print("3. Pour un Shared Drive: S'assurer que le Service Account a les permissions")
print("   appropriées sur le Shared Drive")

