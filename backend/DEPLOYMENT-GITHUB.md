# 🚀 Déploiement Automatique GitHub → Railway

Ce guide vous montre comment configurer le déploiement automatique depuis GitHub vers Railway.

**Avantages:**
- ✅ Déploiement automatique à chaque `git push`
- ✅ Preview deployments pour les Pull Requests
- ✅ Rollback facile vers commits précédents
- ✅ Historique complet des déploiements
- ✅ Pas besoin de Railway CLI pour déployer

---

## 🎯 Option 1: Déploiement Direct depuis GitHub (Recommandé)

### Étape 1: Préparer le Repository GitHub

```bash
# Si pas encore de repo Git
git init
git add .
git commit -m "Initial commit - Léonie v0.2.0"

# Créer le repo sur GitHub (via interface web ou gh CLI)
gh repo create leonie --private --source=. --remote=origin --push

# Ou manuellement:
# 1. Créer un repo sur github.com
# 2. git remote add origin https://github.com/VOTRE_USERNAME/leonie.git
# 3. git push -u origin main
```

### Étape 2: Connecter Railway à GitHub

1. **Aller sur Railway Dashboard**
   - Visitez https://railway.app/new
   - Cliquez sur "Deploy from GitHub repo"

2. **Autoriser Railway**
   - Cliquez sur "Configure GitHub App"
   - Sélectionnez votre compte/organisation
   - Choisissez "Only select repositories"
   - Sélectionnez le repo `leonie`
   - Cliquez "Install & Authorize"

3. **Sélectionner le Repository**
   - Retournez sur Railway
   - Sélectionnez votre repo `leonie` dans la liste
   - Railway détectera automatiquement le Dockerfile

4. **Configurer le Projet**
   - Nom du projet: `leonie-production` (ou autre)
   - Branch de déploiement: `main` (ou `production`)
   - Cliquez "Deploy Now"

### Étape 3: Configurer les Variables d'Environnement

**Sur le Dashboard Railway:**

1. Cliquez sur votre service
2. Onglet "Variables"
3. Cliquez "RAW Editor" pour coller toutes les variables en une fois

**Format RAW Editor:**
```env
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Mistral AI
MISTRAL_API_KEY=votre_cle_mistral
MISTRAL_MODEL_CHAT=mistral-large-latest
MISTRAL_MODEL_VISION=pixtral-large-latest

# Email IMAP (App Password Gmail!)
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_EMAIL=leonie@voxperience.com
IMAP_PASSWORD=xxxx xxxx xxxx xxxx
IMAP_LABEL=INBOX

# Email SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=leonie@voxperience.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_FROM_NAME=Léonie

# Sécurité (générer avec: openssl rand -hex 32)
API_SECRET_KEY=votre_cle_secrete_de_32_caracteres

# CORS (optionnel)
CORS_ORIGINS=*

# Documents
MAX_FILE_SIZE_MB=10
TARGET_PDF_SIZE_MB=1.8
DOCUMENT_TEMP_DIR=/tmp/leonie/documents
```

4. Cliquez "Save"
5. Le service redémarrera automatiquement

### Étape 4: Vérifier le Déploiement

1. **Voir les logs de build:**
   - Onglet "Deployments"
   - Cliquez sur le déploiement en cours
   - Voir les logs en temps réel

2. **Obtenir l'URL:**
   - Onglet "Settings"
   - Section "Networking"
   - Cliquez "Generate Domain"
   - Vous obtiendrez une URL type: `https://leonie-production.up.railway.app`

3. **Tester:**
   ```bash
   curl https://votre-app.railway.app/health
   ```

---

## 🔄 Déploiement Automatique

Une fois configuré, chaque `git push` déclenchera un déploiement automatique!

### Workflow Standard

```bash
# 1. Faire vos modifications localement
vim app/services/document.py

# 2. Tester localement
pytest
uvicorn main:app --reload

# 3. Commit et push
git add .
git commit -m "feat: amélioration traitement documents"
git push origin main

# 4. Railway déploie automatiquement! 🎉
# Voir les logs sur le dashboard Railway
```

### Configuration de la Branche

Par défaut, Railway déploie depuis `main`. Pour changer:

1. Dashboard Railway → Votre service
2. Onglet "Settings"
3. Section "Source"
4. "Branch": sélectionnez `production` ou autre
5. Save

**Stratégie recommandée:**
- **Branche `main`**: Développement, déploiement auto vers environnement de staging
- **Branche `production`**: Production, déploiement auto vers environnement de production

---

## 🔀 Option 2: Migrer d'un Déploiement CLI vers GitHub

Si vous avez déjà déployé avec le script CLI et voulez passer à GitHub:

### Étape 1: Connecter le Repo GitHub

1. **Dashboard Railway** → Votre projet
2. **Settings** → **Source**
3. Cliquez "Connect Repo"
4. Autorisez GitHub et sélectionnez votre repo
5. Choisissez la branche (main)

### Étape 2: Configurer le Déploiement

Railway détectera le Dockerfile automatiquement. Les variables d'environnement sont conservées.

### Étape 3: Déclencher un Déploiement

```bash
git push origin main
```

Railway déploiera depuis GitHub maintenant!

---

## 🎨 Environnements Multiples

Railway permet d'avoir plusieurs environnements (staging, production).

### Configuration Recommandée

**Environnement 1: Staging** (branche `main`)
- URL: `https://leonie-staging.up.railway.app`
- Déploiement auto à chaque push sur `main`
- Variables: `ENVIRONMENT=staging`, `DEBUG=true`

**Environnement 2: Production** (branche `production`)
- URL: `https://leonie-production.up.railway.app`
- Déploiement auto à chaque push sur `production`
- Variables: `ENVIRONMENT=production`, `DEBUG=false`

### Créer un Environnement

1. Dashboard Railway → Votre projet
2. Cliquez "+ New" → "Environment"
3. Nom: `Production`
4. Source: branche `production`
5. Copier les variables depuis staging
6. Ajuster les variables si nécessaire

### Workflow avec Environnements

```bash
# Développement
git checkout main
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push origin main
# → Déploie automatiquement sur staging

# Après tests sur staging, déployer en production
git checkout production
git merge main
git push origin production
# → Déploie automatiquement sur production
```

---

## 🔍 Preview Deployments (Pull Requests)

Railway peut créer un déploiement temporaire pour chaque Pull Request!

### Activer les Preview Deployments

1. Dashboard Railway → Votre service
2. Settings → Deploy
3. "Pull Request Deploys": **Enabled**
4. Save

### Utilisation

```bash
# 1. Créer une branche feature
git checkout -b feature/nouveau-service
git commit -m "WIP: nouveau service"
git push origin feature/nouveau-service

# 2. Créer une Pull Request sur GitHub

# 3. Railway crée automatiquement un déploiement preview
# URL: https://leonie-pr-123.up.railway.app

# 4. Tester sur l'URL preview

# 5. Merger la PR → déploiement automatique sur main
```

---

## 🔧 Configuration Avancée

### Railway.toml (Optionnel)

Créez un fichier `railway.toml` pour une config avancée:

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
numReplicas = 1
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
healthcheckPath = "/health"
healthcheckTimeout = 100
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

### Fichiers à Exclure du Build

Le `.dockerignore` existant est déjà configuré. Vérifiez qu'il contient:

```
.git/
.env
.env.local
__pycache__/
*.pyc
venv/
.vscode/
.idea/
tests/
*.test.py
```

---

## 📊 Monitoring et Logs

### Voir les Logs

**Via Dashboard:**
1. Railway Dashboard → Votre service
2. Onglet "Deployments"
3. Cliquez sur un déploiement
4. Logs en temps réel

**Via CLI (optionnel):**
```bash
railway login
railway link  # Lier au projet
railway logs --tail
```

### Métriques

Dashboard Railway affiche:
- CPU usage
- Memory usage
- Network traffic
- Request count

### Alertes

1. Settings → Notifications
2. Configurer Slack/Discord/Email
3. Recevoir des alertes en cas d'erreur

---

## 🔐 Sécurité

### Secrets GitHub

Pour les GitHub Actions (voir section suivante), utilisez les secrets:

1. GitHub repo → Settings → Secrets and variables → Actions
2. Ajoutez les secrets (pas nécessaire pour Railway auto-deploy)

### Variables d'Environnement

**NE JAMAIS** commiter:
- `.env` ✅ (déjà dans `.gitignore`)
- Clés API
- Mots de passe
- Tokens

**Toujours** configurer sur Railway Dashboard.

---

## 🚀 GitHub Actions (Optionnel)

Pour exécuter des tests **avant** que Railway ne déploie:

Créez `.github/workflows/test.yml` (voir fichier séparé).

Les tests s'exécuteront à chaque push. Si les tests échouent, vous serez notifié (mais Railway déploiera quand même - voir workflow avancé pour bloquer).

---

## 🔄 Rollback

Si un déploiement pose problème:

1. Dashboard Railway → Deployments
2. Trouvez le déploiement précédent (qui fonctionnait)
3. Cliquez sur les 3 points → "Rollback to this deployment"

Ou via Git:

```bash
git log  # Trouver le commit qui fonctionnait
git revert HEAD  # Annuler le dernier commit
git push origin main  # Railway redéploie
```

---

## 📝 Checklist Déploiement GitHub

- [ ] Repo GitHub créé et pushé
- [ ] Railway connecté au repo GitHub
- [ ] Branche de déploiement configurée
- [ ] Variables d'environnement configurées sur Railway
- [ ] App Password Gmail configuré
- [ ] Domaine Railway généré
- [ ] Healthcheck testé (`/health`)
- [ ] Preview deployments activés (optionnel)
- [ ] Environnements multiples configurés (optionnel)
- [ ] GitHub Actions configuré (optionnel)

---

## 💡 Avantages GitHub vs CLI

| Fonctionnalité | CLI | GitHub Auto |
|----------------|-----|-------------|
| Déploiement auto | ❌ | ✅ |
| Preview PRs | ❌ | ✅ |
| Historique commits | ❌ | ✅ |
| Rollback facile | ❌ | ✅ |
| Équipe collaborative | ❌ | ✅ |
| CI/CD intégré | ❌ | ✅ |

**Recommandation:** Utilisez GitHub pour la production!

---

## 🆘 Dépannage

### "Railway can't access my repo"

Vérifiez:
1. GitHub → Settings → Applications → Railway
2. Railway a bien accès au repo
3. Réinstallez l'app GitHub si nécessaire

### "Build failed"

Vérifiez:
1. Logs de build sur Railway Dashboard
2. Dockerfile est valide
3. Toutes les dépendances sont dans `requirements.txt`

### "App crashes after deploy"

Vérifiez:
1. Variables d'environnement configurées
2. Logs d'application: onglet "Logs"
3. Healthcheck: `/health` retourne 200

### Variables manquantes

Railway garde les variables même en changeant de CLI vers GitHub. Vérifiez:
```
Dashboard → Variables → Vérifier toutes les variables requises
```

---

## 🎯 Workflow Recommandé

```bash
# 1. Développement local
git checkout -b feature/ma-feature
# ... modifications ...
pytest  # Tests locaux

# 2. Push et créer PR
git push origin feature/ma-feature
# Créer PR sur GitHub
# → Railway crée preview deployment

# 3. Review et tests sur preview
curl https://leonie-pr-123.up.railway.app/health

# 4. Merge PR
# → Déploiement auto sur staging (main)

# 5. Tests sur staging
curl https://leonie-staging.up.railway.app/test-imap

# 6. Déployer en production
git checkout production
git merge main
git push origin production
# → Déploiement auto sur production
```

---

## 🎉 C'est Fait!

Votre application déploie maintenant automatiquement à chaque `git push`!

**Prochaines étapes:**
- Configurer les alertes
- Mettre en place des environnements multiples
- Activer les preview deployments
- Configurer GitHub Actions pour tests automatiques

Bon déploiement! 🚀
