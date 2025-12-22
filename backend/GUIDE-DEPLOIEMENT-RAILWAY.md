# 🚀 Guide de Déploiement Railway - Étape par Étape

Ce guide vous accompagne pour déployer Léonie sur Railway et tester que tout fonctionne.

---

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir :

- ✅ Un compte Railway (gratuit) : https://railway.app
- ✅ Un repository GitHub avec votre code
- ✅ Toutes les clés API nécessaires :
  - Supabase (URL + KEY)
  - Gmail App Password
  - Mistral API Key
  - Google Drive Service Account JSON
  - Google Drive Master Folder ID

---

## 🎯 Étape 1 : Créer le Projet Railway

1. Allez sur https://railway.app
2. Connectez-vous avec GitHub
3. Cliquez sur **"New Project"**
4. Sélectionnez **"Deploy from GitHub repo"**
5. Choisissez votre repository `leonie`
6. Railway détecte automatiquement le `Dockerfile` et crée le service

**✅ Résultat attendu :** Un nouveau projet Railway avec un service `web` en cours de déploiement.

---

## 🔐 Étape 2 : Configurer les Variables d'Environnement

Dans Railway, allez dans **Variables** (onglet en haut) et ajoutez toutes les variables suivantes :

### Variables Obligatoires

#### 1. Supabase
```bash
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre-clé-api-supabase
```

#### 2. Gmail IMAP
```bash
IMAP_HOST=imap.gmail.com
IMAP_EMAIL=leonie.capitalinfinie@gmail.com
IMAP_PASSWORD=votre-app-password-gmail
IMAP_LABEL=INBOX
```

#### 3. Mistral AI
```bash
MISTRAL_API_KEY=votre-clé-mistral
```

#### 4. Google Drive (OBLIGATOIRE)
```bash
GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"..."}'
GOOGLE_DRIVE_MASTER_FOLDER_ID=1abc_defgh_ijklmnop_qrstuvwxyz
```

**⚠️ IMPORTANT pour GOOGLE_CREDENTIALS_JSON :**
- Copiez le JSON complet depuis votre fichier Service Account
- Tout sur **une seule ligne**
- Entouré de **quotes simples** `'...'`
- Les `\n` dans `private_key` doivent être préservés

**Comment obtenir le JSON :**
1. Ouvrez le fichier JSON téléchargé (ex: `leonie-drive-abc123.json`)
2. Copiez **tout** le contenu (de `{` à `}`)
3. Collez dans Railway en une seule ligne avec quotes simples

#### 5. Sécurité
```bash
API_SECRET_KEY=votre-clé-secrète-aléatoire-minimum-32-caractères
```

Générez une clé secrète :
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 6. SMTP (pour notifications)
```bash
SMTP_EMAIL=leonie.capitalinfinie@gmail.com
SMTP_PASSWORD=votre-app-password-gmail
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_FROM_NAME=Léonie
```

#### 7. Environnement
```bash
ENVIRONMENT=production
```

**⚠️ NE PAS AJOUTER :**
- `PORT` (Railway le définit automatiquement)

---

## 🔍 Étape 3 : Vérifier le Déploiement

### 3.1 Attendre le Build

1. Dans Railway, allez dans **Deployments**
2. Attendez que le build se termine (icône verte ✅)
3. Vérifiez les logs pour voir s'il y a des erreurs

### 3.2 Obtenir l'URL Publique

1. Dans Railway, allez dans **Settings** du service `web`
2. Activez **"Generate Domain"** si ce n'est pas déjà fait
3. Notez l'URL : `https://votre-app.up.railway.app`

### 3.3 Tester l'Application

Utilisez le script de test fourni :

```bash
./test_railway.sh https://votre-app.up.railway.app
```

Ou testez manuellement :

```bash
# Test 1: Health check
curl https://votre-app.up.railway.app/health | jq

# Test 2: Route racine
curl https://votre-app.up.railway.app/ | jq

# Test 3: Test Google Drive
curl -X POST https://votre-app.up.railway.app/test-drive | jq

# Test 4: Test IMAP
curl https://votre-app.up.railway.app/test-imap | jq
```

---

## ✅ Étape 4 : Vérifier que Google Drive Fonctionne

### 4.1 Tester l'Endpoint

```bash
curl -X POST https://votre-app.up.railway.app/test-drive | jq
```

### 4.2 Résultat Attendu

```json
{
  "status": "success",
  "connection": {
    "status": "ok",
    "master_folder_id": "1abc..."
  },
  "folder_creation": {
    "status": "created",
    "folder_id": "1xyz...",
    "folder_name": "TEST_Leonie_Drive"
  },
  "file_upload": {
    "status": "uploaded",
    "file_id": "1def...",
    "filename": "test_leonie_upload.pdf"
  },
  "shareable_link": "https://drive.google.com/file/d/..."
}
```

### 4.3 Vérifier sur Google Drive

1. Allez sur https://drive.google.com
2. Ouvrez le dossier "DOSSIERS_PRETS"
3. Vous devriez voir :
   - Un dossier "TEST_Leonie_Drive"
   - À l'intérieur, un fichier "test_leonie_upload.pdf"

**✅ Si vous voyez le fichier, Google Drive fonctionne !**

---

## 🐛 Dépannage

### Erreur : "Healthcheck failed"

**Causes possibles :**
- Variables d'environnement manquantes
- Erreur au démarrage de l'application
- Timeout du healthcheck

**Solutions :**
1. Vérifier les logs dans Railway → Logs
2. Vérifier que toutes les variables obligatoires sont définies
3. Vérifier que `PORT` n'est PAS dans les variables (Railway le définit automatiquement)
4. Augmenter le timeout dans `railway.json` si nécessaire

### Erreur : "Invalid JSON" (Google Drive)

**Cause :** Le JSON du Service Account est mal formaté.

**Solution :**
1. Vérifier que le JSON est sur une seule ligne
2. Vérifier que les quotes simples `'...'` entourent le JSON
3. Vérifier que les `\n` dans `private_key` sont préservés

### Erreur : "The caller does not have permission" (Google Drive)

**Cause :** Le Service Account n'a pas accès au dossier.

**Solution :**
1. Vérifier que le dossier "DOSSIERS_PRETS" est partagé avec le Service Account
2. Vérifier l'email du Service Account (doit finir par `.iam.gserviceaccount.com`)
3. Permissions : "Editor" (ou "Can edit")

### Erreur : "File not found" (Google Drive)

**Cause :** L'ID du dossier est incorrect.

**Solution :**
1. Ouvrir le dossier "DOSSIERS_PRETS" sur Drive
2. Copier l'ID depuis l'URL (après `/folders/`)
3. Vérifier que `GOOGLE_DRIVE_MASTER_FOLDER_ID` correspond

### Erreur : "API not enabled" (Google Drive)

**Cause :** Google Drive API n'est pas activée.

**Solution :**
1. Aller sur https://console.cloud.google.com/apis/library
2. Chercher "Google Drive API"
3. Cliquer "ENABLE"

---

## 📝 Checklist de Déploiement

Avant de considérer le déploiement comme terminé, vérifiez :

- [ ] Projet Railway créé
- [ ] Service `web` déployé avec succès (icône verte)
- [ ] Toutes les variables d'environnement définies
- [ ] `GOOGLE_CREDENTIALS_JSON` correctement formaté (une ligne, quotes simples)
- [ ] `GOOGLE_DRIVE_MASTER_FOLDER_ID` correct
- [ ] URL publique générée
- [ ] Test `/health` réussi
- [ ] Test `/test-drive` réussi
- [ ] Fichier de test visible sur Google Drive
- [ ] Test `/test-imap` réussi (si configuré)

---

## 🎉 Prochaines Étapes

Une fois le déploiement réussi :

1. **Surveiller les logs** : Railway → Logs pour voir l'activité
2. **Configurer le domaine personnalisé** (optionnel) : Railway → Settings → Custom Domain
3. **Activer les notifications** (optionnel) : Railway → Settings → Notifications
4. **Configurer Redis** (pour plus tard) : Quand les workers seront implémentés

---

## 🔗 Ressources

- [Documentation Railway](https://docs.railway.app)
- [Guide Google Drive Setup](./GOOGLE-DRIVE-SETUP.md)
- [Dépannage Railway](./RAILWAY_TROUBLESHOOTING.md)
- [Script de test](./test_railway.sh)

---

**Bon déploiement ! 🚀**

