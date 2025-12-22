# 🚀 Déploiement Cloudflare via CLI (Wrangler)

Guide pour déployer le frontend Léonie sur Cloudflare Pages via la ligne de commande.

---

## ✅ Prérequis (FAIT)

- [x] Wrangler installé
- [x] Code sur GitHub
- [x] Configuration `wrangler.toml` créée
- [x] Script de déploiement `deploy-cloudflare.sh` créé

---

## 🔐 ÉTAPE 1 : Authentification (À FAIRE)

Exécutez cette commande dans votre terminal :

```bash
wrangler login
```

**Ce qui va se passer** :
1. Un navigateur s'ouvre automatiquement
2. Connectez-vous à votre compte Cloudflare
3. Cliquez sur "Allow" pour autoriser Wrangler
4. Revenez au terminal → vous verrez "Successfully logged in"

**Vérifiez** que vous êtes connecté :

```bash
wrangler whoami
```

Vous devriez voir votre email Cloudflare.

---

## 🚀 ÉTAPE 2 : Déploiement automatique (Ultra simple)

Une fois authentifié, il suffit de lancer le script :

```bash
cd frontend
./deploy-cloudflare.sh
```

**Le script fait TOUT automatiquement** :
- ✅ Vérifie l'authentification
- ✅ Build le projet (`npm run build`)
- ✅ Crée le projet Cloudflare Pages (si première fois)
- ✅ Déploie sur Cloudflare

**Durée** : 2-3 minutes

---

## 🔐 ÉTAPE 3 : Configurer les variables d'environnement

Après le premier déploiement, configurez les variables :

### Option A : Via CLI (Recommandé)

```bash
cd frontend

# Variable 1 : Supabase URL
wrangler pages secret put VITE_SUPABASE_URL --project-name=leonie
# Entrez : https://wybypzuuyxzgdtmslcko.supabase.co

# Variable 2 : Supabase Anon Key
wrangler pages secret put VITE_SUPABASE_ANON_KEY --project-name=leonie
# Entrez : eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind5YnlwenV1eXh6Z2R0bXNsY2tvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU3NzQxNjQsImV4cCI6MjA4MTM1MDE2NH0.duIB8Eqe--DH-6V5W-77B8u00NcByqm6_vLJ7MtDs08

# Variable 3 : API URL (temporaire, à changer après déploiement Railway)
wrangler pages secret put VITE_API_URL --project-name=leonie
# Entrez : http://localhost:8000/api
```

### Option B : Via Dashboard Cloudflare

1. Allez sur https://dash.cloudflare.com/
2. **Workers & Pages** → **leonie**
3. **Settings** → **Environment variables**
4. Ajoutez les 3 variables manuellement

---

## 🔄 ÉTAPE 4 : Redéployer avec les variables

Après avoir ajouté les variables, redéployez :

```bash
cd frontend
./deploy-cloudflare.sh
```

---

## ✅ ÉTAPE 5 : Vérifier le déploiement

### Obtenir l'URL

```bash
wrangler pages project list
```

Vous verrez l'URL de votre projet :
```
leonie: https://leonie.pages.dev
```

Ouvrez cette URL dans votre navigateur !

### Tester

Vous devriez voir :
- ✅ Page de login avec design Capital In Fine
- ✅ Couleurs CIF (#1E3A5F)
- ✅ Interface stylée

---

## 📝 Commandes utiles

### Voir les projets Cloudflare

```bash
wrangler pages project list
```

### Voir les déploiements

```bash
wrangler pages deployment list --project-name=leonie
```

### Voir les variables d'environnement

```bash
wrangler pages secret list --project-name=leonie
```

### Supprimer une variable

```bash
wrangler pages secret delete VARIABLE_NAME --project-name=leonie
```

### Voir les logs

```bash
wrangler pages deployment tail --project-name=leonie
```

---

## 🔄 Déploiements futurs

Pour redéployer après des modifications :

```bash
cd frontend
./deploy-cloudflare.sh
```

**C'est tout !** Le script gère tout automatiquement.

---

## 🎯 Workflow complet

```bash
# 1. Modifier le code
vim src/pages/Dashboard.tsx

# 2. Tester localement
npm run dev

# 3. Déployer
./deploy-cloudflare.sh

# 4. Vérifier
open https://leonie.pages.dev
```

---

## 🐛 Troubleshooting

### "Not logged in"

❌ Problème : Pas authentifié
✅ Solution : `wrangler login`

### "Project not found"

❌ Problème : Projet pas encore créé
✅ Solution : Le script le crée automatiquement au premier déploiement

### "Build failed"

❌ Problème : Erreur de build
✅ Solution : Testez localement d'abord avec `npm run build`

### Variables d'environnement ne fonctionnent pas

❌ Problème : Variables pas définies ou mal configurées
✅ Solution : Vérifiez avec `wrangler pages secret list --project-name=leonie`

---

## 🎉 Avantages de la CLI

- ✅ **Plus rapide** que l'interface web
- ✅ **Automatisable** (scripts, CI/CD)
- ✅ **Reproductible** (même configuration partout)
- ✅ **Versionnable** (wrangler.toml dans Git)

---

## 📞 Besoin d'aide ?

Documentation Wrangler : https://developers.cloudflare.com/pages/get-started/
