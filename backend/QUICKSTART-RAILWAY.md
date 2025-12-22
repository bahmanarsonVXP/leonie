# 🚀 Déploiement Railway - Guide Rapide

## ⚡ Déploiement en 5 Minutes

### 1. Installer Railway CLI

```bash
npm install -g @railway/cli
# ou
brew install railway
```

### 2. S'authentifier

```bash
railway login
```

### 3. Lancer le script automatique

```bash
./deploy-railway.sh
```

Le script vous guidera à travers toutes les étapes!

---

## 📝 Déploiement Manuel (Étape par Étape)

### Étape 1: Authentification

```bash
railway login
railway whoami  # Vérifier que vous êtes bien connecté
```

### Étape 2: Créer/Lier le Projet

**Option A: Nouveau projet**
```bash
railway init
# Suivre les instructions à l'écran
```

**Option B: Projet existant**
```bash
railway link
# Choisir votre projet dans la liste
```

### Étape 3: Variables d'Environnement (CRITIQUE!)

Générez d'abord une clé secrète:
```bash
openssl rand -hex 32
```

Puis configurez les variables **REQUISES**:

```bash
# Supabase
railway variables set SUPABASE_URL="https://xxxxx.supabase.co"
railway variables set SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Mistral AI
railway variables set MISTRAL_API_KEY="votre_cle_mistral"

# Email Gmail (UTILISEZ UN APP PASSWORD!)
railway variables set IMAP_EMAIL="leonie@voxperience.com"
railway variables set IMAP_PASSWORD="xxxx xxxx xxxx xxxx"  # App Password Gmail
railway variables set SMTP_EMAIL="leonie@voxperience.com"
railway variables set SMTP_PASSWORD="xxxx xxxx xxxx xxxx"

# Sécurité
railway variables set API_SECRET_KEY="votre_cle_secrete_de_32_caracteres"

# Application
railway variables set ENVIRONMENT="production"
railway variables set DEBUG="false"
railway variables set LOG_LEVEL="INFO"
```

**⚠️ IMPORTANT: App Password Gmail**
1. Allez sur https://myaccount.google.com/apppasswords
2. Créez un nouveau mot de passe d'application
3. Utilisez ce mot de passe (16 caractères) pour `IMAP_PASSWORD` et `SMTP_PASSWORD`

**Vérifier les variables:**
```bash
railway variables
```

### Étape 4: Déployer

```bash
# Déployer
railway up

# Ou déployer en arrière-plan et voir les logs
railway up --detach
railway logs
```

### Étape 5: Obtenir l'URL et Tester

```bash
# Voir l'URL de votre application
railway domain

# Tester le healthcheck
curl https://votre-app.railway.app/health

# Devrait retourner:
# {
#   "status": "healthy",
#   "timestamp": "...",
#   "version": "0.1.0",
#   "environment": "production"
# }
```

---

## ✅ Checklist Pré-Déploiement

- [ ] Railway CLI installé (`railway --version`)
- [ ] Authentifié (`railway whoami`)
- [ ] App Password Gmail généré
- [ ] Clé API Mistral valide
- [ ] Clé API Supabase valide
- [ ] `API_SECRET_KEY` généré (32+ caractères)
- [ ] Toutes les variables configurées (`railway variables`)
- [ ] Tests locaux réussis (`pytest`)

---

## 🔍 Commandes Utiles Post-Déploiement

```bash
# Voir les logs en temps réel
railway logs --tail

# Ouvrir le dashboard Railway
railway open

# Voir l'URL publique
railway domain

# Redéployer après modifications
railway up

# Voir les variables
railway variables

# Supprimer une variable
railway variables delete NOM_VARIABLE

# Se connecter au shell du conteneur
railway run bash
```

---

## 🧪 Tester l'Application Déployée

Une fois déployée, testez les endpoints:

```bash
# Remplacez YOUR_APP_URL par votre URL Railway
export APP_URL="https://votre-app.railway.app"

# 1. Healthcheck
curl $APP_URL/health

# 2. Info API
curl $APP_URL/api/info

# 3. Test connexion IMAP
curl $APP_URL/test-imap

# 4. Test Mistral AI
curl -X POST $APP_URL/test-mistral \
  -H "Content-Type: application/json" \
  -d '{
    "email_subject": "Nouveau dossier test",
    "email_body": "Test de classification Mistral",
    "courtier_email": "test@test.com"
  }'

# 5. Test traitement document (avec un fichier)
curl -X POST $APP_URL/test-document \
  -F "file=@/chemin/vers/image.jpg"
```

---

## 🐛 Dépannage Rapide

### Déploiement bloqué
```bash
railway logs --deployment  # Voir les logs de build
```

### Variables manquantes
```bash
railway variables  # Lister toutes les variables
```

### Erreur "Port already in use"
Railway gère le port automatiquement via la variable `PORT`. Le Dockerfile est déjà configuré.

### Erreur connexion Gmail
Vérifiez:
1. Vous utilisez un **App Password** (pas votre mot de passe Gmail)
2. L'authentification 2FA est activée sur votre compte Gmail
3. Les variables `IMAP_EMAIL` et `IMAP_PASSWORD` sont correctes

```bash
railway variables | grep IMAP
```

### Erreur Mistral AI
Vérifiez que votre clé API est valide:
```bash
railway variables | grep MISTRAL
```

### Logs complets
```bash
railway logs --tail 500  # Les 500 dernières lignes
```

---

## 📊 Surveillance

Une fois en production, surveillez:

```bash
# Logs en continu
railway logs

# Ouvrir le dashboard (métriques CPU/RAM)
railway open
```

Dans le dashboard Railway, activez les **alertes** pour être notifié en cas d'erreur.

---

## 🔄 Mises à Jour

Après modifications du code:

```bash
# 1. Tester localement
pytest

# 2. Commit (recommandé)
git add .
git commit -m "Description des changements"

# 3. Redéployer
railway up

# 4. Suivre les logs
railway logs
```

---

## 🎯 URLs de Référence

- **Dashboard:** https://railway.app/dashboard
- **Docs Railway:** https://docs.railway.app
- **DEPLOYMENT.md:** Guide complet avec toutes les variables

---

## 💡 Astuces

1. **Démarrez simple:** Déployez d'abord avec les variables minimales, testez le healthcheck
2. **Logs verbeux:** Utilisez `LOG_LEVEL=DEBUG` au début pour diagnostiquer
3. **Double-check:** Vérifiez toujours les variables avec `railway variables`
4. **Backup:** Sauvegardez régulièrement votre base Supabase

---

## 🆘 Besoin d'Aide?

- Voir `DEPLOYMENT.md` pour le guide complet
- Consulter les logs: `railway logs --tail 100`
- Dashboard Railway: `railway open`
- Documentation Railway: https://docs.railway.app

Bon déploiement! 🎉
