# 🚀 Choisir Votre Méthode de Déploiement

Vous avez **3 options** pour déployer Léonie sur Railway. Voici un guide pour choisir.

---

## 📊 Comparaison des 3 Méthodes

| Critère | CLI Manuel | GitHub Auto | GitHub + Actions |
|---------|------------|-------------|------------------|
| **Setup initial** | 5 min | 10 min | 15 min |
| **Déploiement auto** | ❌ Non | ✅ Oui | ✅ Oui |
| **Tests auto** | ❌ Non | ❌ Non | ✅ Oui |
| **Preview PRs** | ❌ Non | ✅ Oui | ✅ Oui |
| **Rollback facile** | ❌ Non | ✅ Oui | ✅ Oui |
| **Équipe** | ⚠️ Difficile | ✅ Facile | ✅ Facile |
| **Complexité** | Simple | Simple | Moyenne |
| **Maintenance** | Manuelle | Automatique | Automatique |

---

## 🎯 Recommandations

### ✅ Pour Vous: GitHub Auto (Option 2)

**Utilisez:** `DEPLOYMENT-GITHUB.md`

**Pourquoi:**
- ✅ Déploiement automatique à chaque `git push`
- ✅ Historique complet sur GitHub
- ✅ Possibilité de rollback facilement
- ✅ Preview deployments pour tester avant merge
- ✅ Facile à gérer en équipe plus tard
- ✅ Pas besoin de Railway CLI pour déployer

**Workflow:**
```bash
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push origin main
# Railway déploie automatiquement! 🎉
```

---

## 📋 Les 3 Options Détaillées

### Option 1: CLI Manuel ⚙️

**Guide:** `deploy-railway.sh`

**Avantages:**
- Setup ultra-rapide (5 min)
- Contrôle total sur chaque déploiement
- Pas besoin de repo GitHub

**Inconvénients:**
- Déploiement manuel à chaque fois
- Difficile de collaborer en équipe
- Pas d'historique des déploiements
- Pas de rollback facile

**Quand l'utiliser:**
- Test rapide
- Projet solo sans Git
- Démo temporaire

**Commandes:**
```bash
./deploy-railway.sh
# Puis à chaque mise à jour:
railway up
```

---

### Option 2: GitHub Auto 🚀 (RECOMMANDÉ)

**Guide:** `DEPLOYMENT-GITHUB.md`

**Avantages:**
- ✅ Déploiement automatique à chaque push
- ✅ Preview deployments pour les PRs
- ✅ Rollback facile via Git
- ✅ Historique complet
- ✅ Collaboration facile
- ✅ Environnements multiples (staging/production)

**Inconvénients:**
- Setup initial un peu plus long (10 min)
- Nécessite un repo GitHub

**Quand l'utiliser:**
- **Production** ✅
- Travail en équipe
- Projet à long terme
- Besoin d'historique et rollback

**Setup:**
1. Créer repo GitHub
2. Connecter Railway au repo
3. Configurer variables sur Railway
4. `git push` → Déploiement auto!

---

### Option 3: GitHub + Actions 🏗️

**Guide:** `DEPLOYMENT-GITHUB.md` + workflows dans `.github/workflows/`

**Avantages:**
- Tous les avantages de l'Option 2
- ✅ Tests automatiques avant déploiement
- ✅ Vérification du code (linting)
- ✅ Notifications sur échecs
- ✅ CI/CD complet

**Inconvénients:**
- Setup un peu plus complexe
- Nécessite configuration GitHub Actions
- Les tests peuvent ralentir le feedback (mais c'est bien!)

**Quand l'utiliser:**
- Production avec équipe
- Besoin de qualité garantie
- Tests critiques
- Plusieurs développeurs

**Setup:**
1. Option 2 (GitHub Auto)
2. Activer les workflows GitHub Actions (déjà créés!)
3. Les tests s'exécutent automatiquement

---

## 🎬 Guide Pas à Pas pour Option 2 (Recommandé)

### Étape 1: Créer le Repo GitHub

```bash
# Si pas encore fait
git init
git add .
git commit -m "Initial commit - Léonie v0.2.0"

# Créer le repo sur GitHub
gh repo create leonie --private --source=. --remote=origin --push

# Ou manuellement sur github.com puis:
git remote add origin https://github.com/VOTRE_USERNAME/leonie.git
git push -u origin main
```

### Étape 2: Connecter Railway

1. Allez sur https://railway.app/new
2. Cliquez "Deploy from GitHub repo"
3. Autorisez Railway à accéder à votre repo
4. Sélectionnez `leonie`
5. Railway détecte le Dockerfile automatiquement

### Étape 3: Configurer les Variables

Sur Railway Dashboard → Variables → RAW Editor:

```env
ENVIRONMENT=production
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJI...
MISTRAL_API_KEY=votre_cle
IMAP_EMAIL=leonie@voxperience.com
IMAP_PASSWORD=xxxx xxxx xxxx xxxx
SMTP_EMAIL=leonie@voxperience.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
API_SECRET_KEY=votre_cle_secrete_32_chars
```

### Étape 4: Déployer

Railway déploie automatiquement dès que vous connectez le repo!

Ensuite, chaque `git push` redéploie automatiquement.

### Étape 5: Tester

```bash
# Obtenir l'URL (ou voir sur Railway Dashboard)
# Tester
curl https://votre-app.railway.app/health
```

---

## 🔄 Migration Entre Options

### CLI → GitHub Auto

Si vous avez commencé avec le CLI et voulez passer à GitHub:

1. Créez un repo GitHub et push votre code
2. Sur Railway Dashboard → Settings → Source
3. "Connect Repo"
4. Sélectionnez votre repo
5. ✅ Déploiement auto activé!

Les variables d'environnement sont conservées.

---

## ⚡ Workflow Quotidien par Option

### Option 1 (CLI):
```bash
# Modifier le code
vim app/services/document.py

# Tester localement
pytest

# Déployer
railway up

# Voir les logs
railway logs
```

### Option 2 (GitHub Auto):
```bash
# Modifier le code
vim app/services/document.py

# Tester localement
pytest

# Commit et push
git add .
git commit -m "feat: amélioration"
git push origin main

# Railway déploie automatiquement!
# Voir les logs sur Railway Dashboard
```

### Option 3 (GitHub + Actions):
```bash
# Modifier le code
vim app/services/document.py

# Commit et push
git add .
git commit -m "feat: amélioration"
git push origin main

# GitHub Actions exécute les tests
# Railway déploie automatiquement si tests OK
# Notification par email si échec
```

---

## 🎯 Ma Recommandation pour Vous

**Utilisez Option 2: GitHub Auto**

**Pourquoi:**
1. Vous travaillerez probablement avec Git (bonne pratique)
2. Le déploiement auto fait gagner beaucoup de temps
3. Preview deployments très utile pour tester avant production
4. Rollback facile si problème
5. Prêt pour le travail en équipe si besoin

**Comment commencer:**

```bash
# 1. Créer repo GitHub
gh repo create leonie --private --source=. --remote=origin --push

# 2. Aller sur Railway et connecter le repo
# → https://railway.app/new → "Deploy from GitHub repo"

# 3. Configurer les variables sur Railway Dashboard

# 4. C'est tout! Chaque git push déploiera automatiquement
```

**Temps:** 10-15 minutes de setup initial, puis **0 temps** pour les déploiements futurs!

---

## 📚 Guides Détaillés

- **Option 1 (CLI):** `QUICKSTART-RAILWAY.md` et `deploy-railway.sh`
- **Option 2 (GitHub Auto):** `DEPLOYMENT-GITHUB.md` ⭐
- **Option 3 (+ Actions):** `DEPLOYMENT-GITHUB.md` + `.github/workflows/`
- **Guide complet:** `DEPLOYMENT.md`

---

## 🆘 Questions Fréquentes

### "Puis-je changer d'option après?"

✅ Oui! Vous pouvez migrer de CLI vers GitHub à tout moment. Les variables d'environnement sont conservées.

### "Dois-je installer Railway CLI?"

- **Option 1:** Oui, obligatoire
- **Option 2 et 3:** Non, optionnel (juste pour voir les logs en CLI)

### "GitHub Actions est obligatoire?"

❌ Non, c'est optionnel. Option 2 (GitHub Auto) fonctionne très bien sans.

### "Combien coûte Railway?"

Railway offre un plan gratuit avec $5 de crédit/mois. Pour Léonie, comptez ~$5-10/mois en production.

### "Puis-je tester avant la production?"

✅ Oui! Créez deux environnements:
- `main` → Staging (tests)
- `production` → Production

Ou utilisez les Preview Deployments pour chaque PR.

---

## 🎉 Prêt à Déployer!

**Ma recommandation:** Suivez `DEPLOYMENT-GITHUB.md` (Option 2)

C'est le meilleur compromis entre simplicité et fonctionnalités!

Bonne chance! 🚀
