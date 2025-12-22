# Guide de Déploiement Railway - Léonie

Ce guide vous accompagne étape par étape pour déployer Léonie sur Railway.

## 📋 Prérequis

- Compte Railway créé sur [railway.app](https://railway.app)
- Railway CLI installé
- Toutes les variables d'environnement prêtes

## 🚀 Étape 1: Installation Railway CLI

```bash
# macOS/Linux
npm install -g @railway/cli

# Ou avec Homebrew (macOS)
brew install railway

# Vérifier l'installation
railway --version
```

## 🔐 Étape 2: Authentification

```bash
# Se connecter à Railway
railway login

# Une fenêtre de navigateur s'ouvrira pour l'authentification
# Suivez les instructions à l'écran
```

## 📦 Étape 3: Initialiser le Projet

```bash
# Dans le répertoire du projet Léonie
cd /Users/bahmanarson/projects/leonie

# Créer un nouveau projet Railway (première fois)
railway init

# Ou lier à un projet existant
railway link
```

## ⚙️ Étape 4: Configurer les Variables d'Environnement

Railway a besoin de toutes vos variables d'environnement. Vous avez deux options:

### Option A: Via l'interface Railway Dashboard

1. Allez sur https://railway.app/dashboard
2. Sélectionnez votre projet
3. Onglet "Variables"
4. Ajoutez toutes les variables du fichier `.env`

### Option B: Via CLI (recommandé)

```bash
# Définir les variables une par une
railway variables set SUPABASE_URL="votre_url_supabase"
railway variables set SUPABASE_KEY="votre_cle_supabase"
railway variables set MISTRAL_API_KEY="votre_cle_mistral"
railway variables set IMAP_EMAIL="leonie@voxperience.com"
railway variables set IMAP_PASSWORD="votre_app_password_gmail"
railway variables set SMTP_EMAIL="leonie@voxperience.com"
railway variables set SMTP_PASSWORD="votre_smtp_password"
railway variables set API_SECRET_KEY="generer_une_cle_secrete"

# ... continuer pour toutes les variables
```

### Variables Requises

Voici la liste complète des variables nécessaires:

**Application:**
- `APP_NAME` (optionnel, défaut: "Léonie")
- `APP_VERSION` (optionnel, défaut: "0.2.0")
- `ENVIRONMENT` (production)
- `DEBUG` (false)
- `LOG_LEVEL` (INFO)

**Supabase:**
- `SUPABASE_URL` ⚠️ REQUIS
- `SUPABASE_KEY` ⚠️ REQUIS
- `SUPABASE_SERVICE_ROLE_KEY` (optionnel)

**Email IMAP:**
- `IMAP_HOST` (défaut: imap.gmail.com)
- `IMAP_PORT` (défaut: 993)
- `IMAP_EMAIL` ⚠️ REQUIS
- `IMAP_PASSWORD` ⚠️ REQUIS (App Password Gmail)
- `IMAP_LABEL` (défaut: INBOX)
- `EMAIL_POLLING_INTERVAL` (300)

**Email SMTP:**
- `SMTP_HOST` (défaut: smtp.gmail.com)
- `SMTP_PORT` (défaut: 587)
- `SMTP_EMAIL` ⚠️ REQUIS
- `SMTP_PASSWORD` ⚠️ REQUIS
- `SMTP_FROM_NAME` (défaut: Léonie)

**Mistral AI:**
- `MISTRAL_API_KEY` ⚠️ REQUIS
- `MISTRAL_MODEL_CHAT` (défaut: mistral-large-latest)
- `MISTRAL_MODEL_VISION` (défaut: pixtral-large-latest)
- `MISTRAL_MAX_TOKENS` (2000)
- `MISTRAL_TEMPERATURE` (0.1)

**Google Drive:**
- `GOOGLE_CREDENTIALS_FILE` (chemin vers service-account.json)
- `GDRIVE_ROOT_FOLDER_ID` (optionnel)

**Sécurité:**
- `API_SECRET_KEY` ⚠️ REQUIS (générer avec: `openssl rand -hex 32`)
- `API_ADMIN_TOKEN` (optionnel)
- `CORS_ORIGINS` (défaut: *)

**Documents:**
- `MAX_FILE_SIZE_MB` (10)
- `TARGET_PDF_SIZE_MB` (1.8)
- `DOCUMENT_TEMP_DIR` (/tmp/leonie/documents)

**Redis:**
- `REDIS_URL` (Railway peut fournir via service Redis)

## 🏗️ Étape 5: Vérifier la Configuration Docker

Le `Dockerfile` est prêt et optimisé pour Railway. Il installe automatiquement:
- LibreOffice (conversion Office → PDF)
- Ghostscript (compression PDF)
- Poppler (manipulation PDF)

Railway détectera automatiquement le Dockerfile.

## 🚢 Étape 6: Déployer

```bash
# Déployer sur Railway
railway up

# Ou déployer et voir les logs en temps réel
railway up --detach
railway logs
```

Le déploiement prendra environ 5-10 minutes (installation des dépendances système).

## ✅ Étape 7: Vérifier le Déploiement

```bash
# Voir l'URL de votre application
railway domain

# Tester le healthcheck
curl https://votre-app.railway.app/health

# Tester l'endpoint API info
curl https://votre-app.railway.app/api/info

# Voir les logs
railway logs --tail
```

## 🔍 Commandes Utiles

```bash
# Voir les variables d'environnement
railway variables

# Ouvrir le dashboard
railway open

# Voir les logs en temps réel
railway logs

# Redéployer après modifications
railway up

# Se connecter au shell du conteneur
railway run bash

# Supprimer le déploiement
railway down
```

## 🐛 Dépannage

### Erreur: "LibreOffice n'est pas installé"
Le Dockerfile devrait installer LibreOffice automatiquement. Si l'erreur persiste:
1. Vérifier les logs de build: `railway logs --deployment`
2. Le script `install_dependencies.sh` s'est-il exécuté correctement?

### Erreur: "Ghostscript n'est pas installé"
Idem, devrait être installé par le Dockerfile. Vérifier les logs de build.

### Erreur de connexion Supabase
Vérifier que `SUPABASE_URL` et `SUPABASE_KEY` sont correctement configurés:
```bash
railway variables
```

### Erreur de connexion IMAP
Pour Gmail, assurez-vous d'utiliser un **App Password** et non votre mot de passe Gmail:
1. Allez sur https://myaccount.google.com/apppasswords
2. Générez un nouveau mot de passe d'application
3. Utilisez-le pour `IMAP_PASSWORD`

### Port déjà utilisé
Railway définit automatiquement la variable `PORT`. Le Dockerfile est configuré pour l'utiliser:
```dockerfile
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Logs d'erreur
```bash
# Voir les logs détaillés
railway logs --tail 100

# Logs d'un déploiement spécifique
railway logs --deployment <deployment-id>
```

## 📊 Surveillance

Une fois déployé, surveillez:
- Healthcheck: `/health` (doit retourner `{"status": "healthy"}`)
- Logs: `railway logs --tail`
- Métriques CPU/RAM: Dashboard Railway

## 🔄 Mise à Jour du Code

Après modifications locales:

```bash
# Commit vos changements (optionnel mais recommandé)
git add .
git commit -m "Description des changements"

# Redéployer
railway up

# Suivre les logs
railway logs
```

## 🚨 Variables Sensibles

**NE JAMAIS** commiter dans Git:
- `.env` (déjà dans `.gitignore`)
- `service-account.json` (credentials Google)
- Clés API Mistral/Supabase

Toutes ces variables doivent être configurées **uniquement sur Railway**.

## 📝 Checklist Pré-Déploiement

- [ ] Railway CLI installé et authentifié
- [ ] Projet Railway créé/lié
- [ ] Toutes les variables d'environnement configurées
- [ ] App Password Gmail généré
- [ ] Clé API Mistral valide
- [ ] Clé API Supabase valide
- [ ] `API_SECRET_KEY` généré (32+ caractères)
- [ ] Dockerfile et requirements.txt à jour
- [ ] Tests locaux passent

## 🎯 URLs Importantes

- **Dashboard Railway:** https://railway.app/dashboard
- **Documentation Railway:** https://docs.railway.app
- **Votre app:** `railway domain` pour obtenir l'URL

## 💡 Conseils

1. **Commencez petit:** Déployez d'abord sans toutes les features, testez le healthcheck
2. **Logs verbeux:** Utilisez `LOG_LEVEL=DEBUG` au début, puis `INFO` en prod
3. **Variables:** Double-vérifiez toutes les variables avec `railway variables`
4. **Monitoring:** Activez les alertes Railway pour être notifié des erreurs
5. **Backup:** Railway fait des snapshots, mais sauvegardez votre DB Supabase régulièrement

## 🎉 Prêt!

Une fois déployé, vous pouvez:
- Tester `/test-imap` pour vérifier la connexion Gmail
- Tester `/test-mistral` pour classifier des emails
- Tester `/test-document` pour traiter des fichiers
- Appeler `/cron/check-emails` pour déclencher le polling manuel

Bonne chance! 🚀
