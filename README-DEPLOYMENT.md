# 📦 Guide de Déploiement Léonie

Bienvenue! Ce README vous aide à choisir et suivre le bon guide pour déployer Léonie sur Railway.

---

## 🎯 Démarrage Rapide

**Vous voulez déployer depuis GitHub avec auto-deploy?** (Recommandé)

➡️ **Lisez:** `DEPLOIEMENT-CHOIX.md` puis suivez `DEPLOYMENT-GITHUB.md`

---

## 📚 Guides Disponibles

### 1. 🔍 Choisir Votre Méthode

**Fichier:** `DEPLOIEMENT-CHOIX.md`

**Contenu:**
- Comparaison des 3 méthodes de déploiement
- Recommandations selon votre cas
- Tableau comparatif
- Workflows quotidiens

**Lisez en premier!**

---

### 2. 🚀 Déploiement GitHub Auto (Recommandé)

**Fichier:** `DEPLOYMENT-GITHUB.md`

**Contenu:**
- Déploiement automatique depuis GitHub
- Preview deployments pour PRs
- Environnements multiples (staging/production)
- Rollback facile
- Migration depuis CLI

**Pour:**
- Production
- Travail en équipe
- Déploiement automatique à chaque `git push`

**Temps:** 10-15 minutes setup initial

---

### 3. ⚡ Déploiement Rapide CLI

**Fichiers:**
- `QUICKSTART-RAILWAY.md` (guide rapide)
- `deploy-railway.sh` (script automatique)

**Contenu:**
- Déploiement rapide en 5 minutes
- Script interactif
- Commandes essentielles

**Pour:**
- Test rapide
- Démo
- Premier déploiement avant de migrer vers GitHub

**Temps:** 5 minutes

**Commandes:**
```bash
./deploy-railway.sh  # Script guidé
# ou
railway login
railway init
railway up
```

---

### 4. 📖 Guide Complet

**Fichier:** `DEPLOYMENT.md`

**Contenu:**
- Toutes les variables d'environnement détaillées
- Configuration avancée
- Dépannage approfondi
- Checklist complète

**Pour:**
- Référence complète
- Problèmes spécifiques
- Configuration avancée

---

## 🏗️ Workflows GitHub Actions (Optionnel)

**Fichiers:** `.github/workflows/`
- `test.yml` - Tests automatiques
- `deploy-production.yml` - Déploiement contrôlé

**Pour:**
- Tests automatiques avant déploiement
- CI/CD complet
- Équipe avec processus qualité

**Setup:** Automatique si vous utilisez GitHub!

---

## 🎯 Quelle Méthode Choisir?

### Vous êtes seul développeur?
➡️ **GitHub Auto** (`DEPLOYMENT-GITHUB.md`)

### Vous travaillez en équipe?
➡️ **GitHub Auto + Actions** (`DEPLOYMENT-GITHUB.md` + workflows)

### Vous voulez tester rapidement?
➡️ **CLI** (`./deploy-railway.sh`)

### Vous voulez tous les détails?
➡️ **Guide Complet** (`DEPLOYMENT.md`)

---

## ⚡ Résumé des Étapes (GitHub Auto)

```bash
# 1. Créer repo GitHub
gh repo create leonie --private --source=. --remote=origin --push

# 2. Aller sur Railway
# → https://railway.app/new
# → "Deploy from GitHub repo"
# → Sélectionner votre repo

# 3. Configurer les variables sur Railway Dashboard
# (voir DEPLOYMENT-GITHUB.md pour la liste)

# 4. Railway déploie automatiquement!

# 5. Chaque git push redéploie automatiquement
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push origin main
# → Déploiement auto! 🎉
```

---

## 📋 Checklist Pré-Déploiement

Avant de commencer, assurez-vous d'avoir:

**Comptes et Accès:**
- [ ] Compte Railway créé (railway.app)
- [ ] Compte GitHub (si déploiement GitHub)
- [ ] Railway CLI installé (optionnel pour GitHub)

**Credentials:**
- [ ] App Password Gmail généré (https://myaccount.google.com/apppasswords)
- [ ] Clé API Mistral
- [ ] URL + Clé Supabase
- [ ] Clé secrète générée (`openssl rand -hex 32`)

**Code:**
- [ ] Tests locaux passent (`pytest`)
- [ ] `.env` configuré localement
- [ ] Git repo initialisé (si GitHub)

---

## 🔐 Variables d'Environnement Requises

**Minimum requis pour démarrer:**

```env
# Supabase (REQUIS)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJI...

# Mistral AI (REQUIS)
MISTRAL_API_KEY=votre_cle_mistral

# Email Gmail - App Password! (REQUIS)
IMAP_EMAIL=leonie@voxperience.com
IMAP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_EMAIL=leonie@voxperience.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx

# Sécurité (REQUIS)
API_SECRET_KEY=generer_avec_openssl_rand_hex_32

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

**Voir guide complet pour toutes les variables:** `DEPLOYMENT.md`

---

## 🧪 Tester Après Déploiement

```bash
# Remplacez par votre URL Railway
export APP_URL="https://votre-app.railway.app"

# 1. Healthcheck
curl $APP_URL/health
# Doit retourner: {"status":"healthy",...}

# 2. Info API
curl $APP_URL/api/info

# 3. Test connexion IMAP
curl $APP_URL/test-imap

# 4. Test Mistral AI
curl -X POST $APP_URL/test-mistral \
  -H "Content-Type: application/json" \
  -d '{"email_subject":"Test","email_body":"Test Mistral"}'

# 5. Test traitement document
curl -X POST $APP_URL/test-document \
  -F "file=@test.jpg"
```

---

## 🆘 Problèmes Courants

### "Je ne sais pas quelle méthode choisir"
➡️ Lisez `DEPLOIEMENT-CHOIX.md`

### "Le déploiement échoue"
➡️ Vérifiez les logs sur Railway Dashboard
➡️ Consultez la section Dépannage dans `DEPLOYMENT.md`

### "Les variables d'environnement ne fonctionnent pas"
➡️ Vérifiez qu'elles sont configurées sur Railway (pas en local)
➡️ Utilisez `railway variables` (CLI) ou Dashboard

### "App Password Gmail ne fonctionne pas"
➡️ Vérifiez que l'authentification 2FA est activée
➡️ Générez un nouveau App Password: https://myaccount.google.com/apppasswords
➡️ Utilisez le format: `xxxx xxxx xxxx xxxx` (16 caractères)

### "Ghostscript/LibreOffice manquant"
➡️ Le Dockerfile les installe automatiquement
➡️ Vérifiez les logs de build sur Railway

---

## 📊 Architecture de Déploiement

```
┌─────────────────┐
│  GitHub Repo    │
│  (votre code)   │
└────────┬────────┘
         │ git push
         ↓
┌─────────────────┐
│ GitHub Actions  │ (Optionnel)
│ - Tests auto    │
│ - Linting       │
└────────┬────────┘
         │ webhook
         ↓
┌─────────────────┐
│    Railway      │
│ - Build Docker  │
│ - LibreOffice   │
│ - Ghostscript   │
│ - Deploy        │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Léonie App     │
│  (production)   │
│  https://...    │
└─────────────────┘
         │
         ├─→ Supabase (database)
         ├─→ Mistral AI (classification)
         ├─→ Gmail (IMAP/SMTP)
         └─→ Google Drive (futur)
```

---

## 🎉 Prochaines Étapes Après Déploiement

1. **Tester tous les endpoints** (voir section tests ci-dessus)
2. **Configurer les alertes** sur Railway Dashboard
3. **Créer environnement staging** (optionnel mais recommandé)
4. **Activer Preview Deployments** pour les PRs
5. **Configurer un domaine personnalisé** (optionnel)
6. **Mettre en place la surveillance** (logs, métriques)

---

## 🔗 Liens Utiles

- **Railway Dashboard:** https://railway.app/dashboard
- **Railway Docs:** https://docs.railway.app
- **GitHub Actions Docs:** https://docs.github.com/en/actions
- **App Password Gmail:** https://myaccount.google.com/apppasswords
- **Mistral AI:** https://console.mistral.ai

---

## 📞 Support

- **Logs Railway:** Dashboard → Deployments → Voir logs
- **Logs en CLI:** `railway logs --tail`
- **Variables:** `railway variables` ou Dashboard
- **Status:** `curl https://votre-app.railway.app/health`

---

## 🚀 C'est Parti!

**Pour commencer maintenant:**

1. Lisez `DEPLOIEMENT-CHOIX.md` (5 min)
2. Suivez le guide recommandé (10-15 min)
3. Testez votre déploiement
4. Profitez du déploiement automatique! 🎉

**Questions?** Consultez les guides détaillés ou les sections dépannage.

Bon déploiement! 🚀
