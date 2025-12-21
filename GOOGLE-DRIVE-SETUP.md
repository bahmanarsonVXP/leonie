# 📁 Configuration Google Drive - Guide Complet

Ce guide vous accompagne étape par étape pour configurer Google Drive avec Léonie.

---

## 🎯 Vue d'Ensemble

Léonie utilise un **Service Account** Google pour accéder à Google Drive. Cela permet:
- ✅ Pas besoin d'authentification OAuth utilisateur
- ✅ Automatisation complète
- ✅ Accès programmatique sécurisé
- ✅ Permissions granulaires par dossier

**Architecture:**
```
Google Cloud Console
    ↓
Service Account (leonie@projet.iam.gserviceaccount.com)
    ↓
Google Drive → Dossier "DOSSIERS_PRETS" (partagé avec le Service Account)
    ↓
Léonie → Upload fichiers via Service Account
```

---

## 📋 Étape 1: Créer un Projet Google Cloud

### 1.1 Accéder à Google Cloud Console

Allez sur: https://console.cloud.google.com

### 1.2 Créer un Nouveau Projet

1. Cliquez sur le sélecteur de projet en haut (à côté de "Google Cloud")
2. Cliquez "NEW PROJECT"
3. Remplissez:
   - **Project name:** `leonie-drive` (ou autre nom)
   - **Organization:** Votre organisation (si applicable)
   - **Location:** Laissez par défaut ou choisissez
4. Cliquez "CREATE"
5. Attendez quelques secondes que le projet soit créé
6. Sélectionnez le nouveau projet dans le sélecteur

---

## 📋 Étape 2: Activer Google Drive API

### 2.1 Accéder au Catalogue d'APIs

1. Dans le menu hamburger (☰) en haut à gauche
2. **APIs & Services** → **Library**
3. Ou allez directement sur: https://console.cloud.google.com/apis/library

### 2.2 Activer Drive API

1. Cherchez "Google Drive API"
2. Cliquez sur le résultat "Google Drive API"
3. Cliquez "ENABLE"
4. Attendez l'activation (quelques secondes)

✅ L'API est maintenant activée pour votre projet!

---

## 📋 Étape 3: Créer un Service Account

### 3.1 Accéder aux Service Accounts

1. Menu hamburger (☰) → **IAM & Admin** → **Service Accounts**
2. Ou allez sur: https://console.cloud.google.com/iam-admin/serviceaccounts

### 3.2 Créer le Service Account

1. Cliquez "**+ CREATE SERVICE ACCOUNT**" en haut
2. Remplissez **Step 1: Service account details**:
   - **Service account name:** `Leonie Drive Service`
   - **Service account ID:** `leonie-drive` (généré automatiquement)
   - **Description:** `Service account pour Léonie - gestion Google Drive`
3. Cliquez "**CREATE AND CONTINUE**"

### 3.3 Accorder les Permissions (Step 2)

**IMPORTANT:** Ne donnez AUCUN rôle au niveau du projet!
- Laissez "Select a role" vide
- Cliquez "**CONTINUE**"

**Pourquoi?** Le Service Account n'a pas besoin d'accès au projet entier. Il aura accès uniquement aux dossiers Drive que vous partagerez avec lui.

### 3.4 Finaliser (Step 3)

- Laissez vide (pas besoin d'accorder l'accès à d'autres utilisateurs)
- Cliquez "**DONE**"

✅ Le Service Account est créé!

**Notez l'email du Service Account:**
```
leonie-drive@votre-projet.iam.gserviceaccount.com
```

---

## 📋 Étape 4: Créer et Télécharger la Clé JSON

### 4.1 Accéder aux Clés

1. Dans la liste des Service Accounts, cliquez sur celui que vous venez de créer
2. Onglet "**KEYS**"

### 4.2 Créer une Nouvelle Clé

1. Cliquez "**ADD KEY**" → "**Create new key**"
2. Choisissez le type: "**JSON**"
3. Cliquez "**CREATE**"

Un fichier JSON est téléchargé automatiquement (ex: `leonie-drive-abc123.json`)

**⚠️ IMPORTANT:**
- Ce fichier contient des credentials sensibles
- Ne JAMAIS le committer dans Git
- Garder en lieu sûr
- Ne jamais partager publiquement

---

## 📋 Étape 5: Créer le Dossier Maître sur Google Drive

### 5.1 Aller sur Google Drive

Allez sur: https://drive.google.com

### 5.2 Créer le Dossier

1. Cliquez "**+ New**" → "**New folder**"
2. Nom du dossier: `DOSSIERS_PRETS`
3. Cliquez "**Create**"

### 5.3 Partager avec le Service Account

1. **Clic droit** sur le dossier "DOSSIERS_PRETS" → "**Share**"
2. Dans "Add people, groups, and calendar events":
   - Collez l'email du Service Account:
     ```
     leonie-drive@votre-projet.iam.gserviceaccount.com
     ```
3. Permissions: "**Editor**" (ou "Can edit")
4. **Décochez** "Notify people" (pas besoin de notification)
5. Cliquez "**Share**"

✅ Le Service Account a maintenant accès au dossier!

### 5.4 Copier l'ID du Dossier

1. Ouvrez le dossier "DOSSIERS_PRETS"
2. Regardez l'URL dans le navigateur:
   ```
   https://drive.google.com/drive/folders/1abc_defgh_ijklmnop_qrstuvwxyz
                                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                            C'EST L'ID DU DOSSIER
   ```
3. Copiez cet ID (environ 30-40 caractères)

**Exemple d'ID:** `1abc_defgh_ijklmnop_qrstuvwxyz`

---

## 📋 Étape 6: Configurer les Variables d'Environnement

### 6.1 Préparer le JSON du Service Account

1. Ouvrez le fichier JSON téléchargé (ex: `leonie-drive-abc123.json`)
2. Il ressemble à ceci:

```json
{
  "type": "service_account",
  "project_id": "leonie-drive-123456",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBA...\n-----END PRIVATE KEY-----\n",
  "client_email": "leonie-drive@leonie-drive-123456.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

3. Copiez **TOUT** le contenu (du premier `{` au dernier `}`)

### 6.2 Ajouter dans .env

**Méthode 1: Une Ligne (Recommandé pour production)**

Dans votre fichier `.env`, ajoutez:

```bash
GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"leonie-drive-123456","private_key_id":"abc123...","private_key":"-----BEGIN PRIVATE KEY-----\nMIIEvQIBA...\n-----END PRIVATE KEY-----\n","client_email":"leonie-drive@leonie-drive-123456.iam.gserviceaccount.com","client_id":"123456789","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/..."}'
```

**IMPORTANT:**
- Tout sur une seule ligne
- Entouré de quotes simples `'...'`
- Les `\n` dans la clé privée doivent être préservés

**Méthode 2: Multi-lignes (Plus lisible pour dev local)**

```bash
GOOGLE_CREDENTIALS_JSON='{
  "type": "service_account",
  "project_id": "leonie-drive-123456",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBA...\n-----END PRIVATE KEY-----\n",
  "client_email": "leonie-drive@leonie-drive-123456.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}'
```

### 6.3 Ajouter l'ID du Dossier

```bash
GOOGLE_DRIVE_MASTER_FOLDER_ID=1abc_defgh_ijklmnop_qrstuvwxyz
```

Remplacez par l'ID que vous avez copié à l'Étape 5.4.

---

## 📋 Étape 7: Tester la Configuration

### 7.1 Démarrer l'Application

```bash
uvicorn main:app --reload
```

### 7.2 Tester l'Endpoint

```bash
curl -X POST http://localhost:8000/test-drive | jq
```

**Résultat attendu:**

```json
{
  "status": "success",
  "connection": {
    "status": "ok",
    "master_folder_id": "1abc_defgh_ijklmnop_qrstuvwxyz"
  },
  "folder_creation": {
    "status": "created",
    "folder_id": "1xyz...",
    "folder_name": "TEST_Leonie_Drive"
  },
  "file_upload": {
    "status": "uploaded",
    "file_id": "1def...",
    "filename": "test_leonie_upload.pdf",
    "folder_id": "1xyz..."
  },
  "shareable_link": "https://drive.google.com/file/d/1def.../view"
}
```

### 7.3 Vérifier sur Google Drive

1. Allez sur https://drive.google.com
2. Ouvrez le dossier "DOSSIERS_PRETS"
3. Vous devriez voir:
   - Un dossier "TEST_Leonie_Drive"
   - À l'intérieur, un fichier "test_leonie_upload.pdf"

✅ **C'est bon! Google Drive fonctionne!**

---

## 🔒 Sécurité

### ⚠️ À FAIRE

- ✅ Ajouter `.env` dans `.gitignore` (déjà fait)
- ✅ Ne jamais committer le fichier JSON du Service Account
- ✅ Utiliser des variables d'environnement pour la production
- ✅ Garder le fichier JSON en lieu sûr (gestionnaire de mots de passe)

### ❌ À NE PAS FAIRE

- ❌ Committer `.env` dans Git
- ❌ Partager le JSON du Service Account publiquement
- ❌ Uploader le JSON sur GitHub/GitLab
- ❌ Envoyer le JSON par email non sécurisé

### 🔐 Pour Railway/Production

Sur Railway Dashboard:
1. Variables → RAW Editor
2. Coller:
   ```env
   GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
   GOOGLE_DRIVE_MASTER_FOLDER_ID=1abc...xyz
   ```

**Astuce:** Utilisez des quotes simples pour éviter les problèmes d'échappement!

---

## 🎯 Structure des Dossiers sur Drive

Une fois configuré, Léonie créera cette structure automatiquement:

```
DOSSIERS_PRETS/                         (Dossier maître, partagé avec Service Account)
├── Courtier_Bahman_Arson/             (Un dossier par courtier)
│   ├── CLIENT_Jean_Dupont/            (Un dossier par client)
│   │   ├── Bulletin_Salaire_1.pdf
│   │   ├── Bulletin_Salaire_2.pdf
│   │   ├── Carte_Identite_Recto_Verso.pdf
│   │   └── ...
│   └── CLIENT_Marie_Martin/
│       └── ...
├── Courtier_Sophie_Dubois/
│   └── ...
└── TEST_Leonie_Drive/                 (Créé par /test-drive)
    └── test_leonie_upload.pdf
```

**Nomenclature:**
- Courtiers: `Courtier_Prenom_Nom`
- Clients: `CLIENT_Prenom_Nom`
- Fichiers: Noms descriptifs en français

---

## 🐛 Dépannage

### Erreur: "Invalid JSON"

**Cause:** Le JSON du Service Account est malformé.

**Solution:**
1. Vérifiez que vous avez copié tout le JSON (de `{` à `}`)
2. Les `\n` dans `private_key` doivent être préservés
3. Utilisez des quotes simples `'...'` autour du JSON

### Erreur: "The caller does not have permission"

**Cause:** Le Service Account n'a pas accès au dossier.

**Solution:**
1. Vérifiez que vous avez partagé le dossier "DOSSIERS_PRETS" avec le Service Account
2. Vérifiez l'email du Service Account (doit finir par `.iam.gserviceaccount.com`)
3. Permissions: "Editor" (ou "Can edit")

### Erreur: "File not found"

**Cause:** L'ID du dossier est incorrect.

**Solution:**
1. Ouvrez le dossier "DOSSIERS_PRETS" sur Drive
2. Copiez l'ID depuis l'URL (après `/folders/`)
3. Vérifiez que `GOOGLE_DRIVE_MASTER_FOLDER_ID` correspond

### Erreur: "API not enabled"

**Cause:** Google Drive API n'est pas activée.

**Solution:**
1. https://console.cloud.google.com/apis/library
2. Cherchez "Google Drive API"
3. Cliquez "ENABLE"

---

## 📚 Ressources

- **Google Cloud Console:** https://console.cloud.google.com
- **Google Drive:** https://drive.google.com
- **Service Account Docs:** https://cloud.google.com/iam/docs/service-account-overview
- **Drive API Docs:** https://developers.google.com/drive/api/guides/about-sdk

---

## ✅ Checklist Finale

- [ ] Projet Google Cloud créé
- [ ] Google Drive API activée
- [ ] Service Account créé
- [ ] Clé JSON téléchargée et sécurisée
- [ ] Dossier "DOSSIERS_PRETS" créé sur Drive
- [ ] Dossier partagé avec le Service Account (Editor)
- [ ] ID du dossier copié
- [ ] `GOOGLE_CREDENTIALS_JSON` configuré dans `.env`
- [ ] `GOOGLE_DRIVE_MASTER_FOLDER_ID` configuré dans `.env`
- [ ] Test `/test-drive` réussi
- [ ] Fichier de test visible sur Google Drive

**Une fois tout coché, Google Drive est prêt! 🎉**

---

## 🚀 Prochaines Étapes

Maintenant que Google Drive est configuré, vous pouvez:

1. **Utiliser le service dans le code:**
   ```python
   from app.services.drive import DriveManager

   drive = DriveManager()
   folder_id = drive.create_courtier_folder("Dupont", "Jean")
   file_id = drive.upload_file(pdf_path, folder_id)
   link = drive.get_shareable_link(file_id)
   ```

2. **Tester l'upload de documents:**
   - Convertir un document avec `/test-document`
   - Upload sur Drive avec le service
   - Vérifier sur Google Drive

3. **Intégrer dans les workflows:**
   - Session 6: Workflows automatisés
   - Upload automatique après traitement documents
   - Organisation par courtier/client

Bon courage! 🚀
