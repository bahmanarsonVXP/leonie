# 🚀 Déploiement Frontend sur Cloudflare Pages

Guide pas à pas pour déployer le frontend Léonie sur Cloudflare Pages depuis le monorepo GitHub.

---

## ✅ Prérequis (FAIT)

- [x] Code sur GitHub : `https://github.com/bahmanarsonVXP/leonie`
- [x] Structure monorepo : `backend/` et `frontend/`
- [x] Credentials Supabase disponibles

---

## 📋 ÉTAPE 2 : Variables d'environnement à préparer

Vous aurez besoin de ces 3 variables pour Cloudflare :

```bash
VITE_SUPABASE_URL=https://wybypzuuyxzgdtmslcko.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind5YnlwenV1eXh6Z2R0bXNsY2tvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU3NzQxNjQsImV4cCI6MjA4MTM1MDE2NH0.duIB8Eqe--DH-6V5W-77B8u00NcByqm6_vLJ7MtDs08
VITE_API_URL=https://votre-backend-railway.up.railway.app/api
```

**Note** : Remplacez `votre-backend-railway.up.railway.app` par l'URL réelle de votre backend Railway une fois déployé.

---

## 🌐 ÉTAPE 3 : Créer le projet Cloudflare Pages

### 3.1 Se connecter à Cloudflare

1. Allez sur **https://dash.cloudflare.com/**
2. Connectez-vous avec votre compte
3. Dans le menu de gauche, cliquez sur **Workers & Pages**

### 3.2 Créer un nouveau projet

1. Cliquez sur **Create application**
2. Sélectionnez l'onglet **Pages**
3. Cliquez sur **Connect to Git**

### 3.3 Connecter le repo GitHub

1. Si première fois : **Autoriser Cloudflare** à accéder à GitHub
2. Sélectionnez le repo : **`bahmanarsonVXP/leonie`**
3. Cliquez sur **Begin setup**

---

## ⚙️ ÉTAPE 4 : Configurer le Build

Dans la page de configuration, remplissez :

### Build Configuration

| Paramètre | Valeur |
|-----------|--------|
| **Project name** | `leonie-frontend` (ou autre nom) |
| **Production branch** | `main` |
| **Framework preset** | **Vite** |
| **Build command** | `npm run build` |
| **Build output directory** | `dist` |
| **Root directory (Path)** | **`frontend`** ⚠️ IMPORTANT |

**⚠️ CRITIQUE** : Le **Root directory** DOIT être `frontend` pour que Cloudflare build depuis le bon dossier du monorepo.

### Screenshot de référence

```
┌─────────────────────────────────────────────────────┐
│ Root directory (Path)                               │
│ ┌─────────────────────────────────────────────────┐ │
│ │ frontend                                        │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ Build command                                       │
│ ┌─────────────────────────────────────────────────┐ │
│ │ npm run build                                   │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ Build output directory                              │
│ ┌─────────────────────────────────────────────────┐ │
│ │ dist                                            │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 🔐 ÉTAPE 5 : Configurer les variables d'environnement

### 5.1 Dans la page de configuration

Scrollez vers le bas jusqu'à la section **Environment variables**

### 5.2 Ajouter les 3 variables

Cliquez sur **Add variable** pour chacune :

#### Variable 1 : VITE_SUPABASE_URL

```
Variable name: VITE_SUPABASE_URL
Value: https://wybypzuuyxzgdtmslcko.supabase.co
```

#### Variable 2 : VITE_SUPABASE_ANON_KEY

```
Variable name: VITE_SUPABASE_ANON_KEY
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind5YnlwenV1eXh6Z2R0bXNsY2tvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU3NzQxNjQsImV4cCI6MjA4MTM1MDE2NH0.duIB8Eqe--DH-6V5W-77B8u00NcByqm6_vLJ7MtDs08
```

#### Variable 3 : VITE_API_URL (temporaire)

```
Variable name: VITE_API_URL
Value: http://localhost:8000/api
```

**Note** : Vous changerez cette valeur plus tard avec l'URL Railway.

### 5.3 Screenshot de référence

```
┌─────────────────────────────────────────────────────┐
│ Environment variables                               │
│                                                     │
│ VITE_SUPABASE_URL                                  │
│ https://wybypzuuyxzgdtmslcko.supabase.co          │
│                                                     │
│ VITE_SUPABASE_ANON_KEY                             │
│ eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVC...            │
│                                                     │
│ VITE_API_URL                                       │
│ http://localhost:8000/api                          │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 ÉTAPE 6 : Lancer le déploiement

1. **Vérifiez** que tout est correct :
   - Root directory = `frontend`
   - Build command = `npm run build`
   - Output directory = `dist`
   - 3 variables d'environnement ajoutées

2. Cliquez sur **Save and Deploy**

3. **Attendez** le build (2-3 minutes)

---

## ✅ ÉTAPE 7 : Vérifier le déploiement

### 7.1 Build réussi

Vous devriez voir :
```
✓ Build successful
✓ Deployment complete
```

### 7.2 Accéder au site

Cloudflare vous donnera une URL :
```
https://leonie-frontend.pages.dev
```

Cliquez dessus pour ouvrir votre application !

### 7.3 Tester la connexion

1. Ouvrez l'URL Cloudflare
2. Vous devriez voir la **page de login** avec le design Capital In Fine
3. **Couleurs CIF** appliquées (bleu #1E3A5F)
4. Formulaire de connexion stylé

**⚠️ Note** : Le login ne fonctionnera pas encore complètement car le backend n'est pas déployé (VITE_API_URL pointe vers localhost).

---

## 🔧 ÉTAPE 8 : Déploiements automatiques

### Désormais, à chaque push sur GitHub :

```bash
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push origin main
```

**Cloudflare détecte automatiquement** les changements dans `frontend/` et rebuild !

---

## 📝 ÉTAPE 9 : Mettre à jour l'URL API (après déploiement Railway)

Une fois le backend déployé sur Railway :

1. Allez dans **Cloudflare Dashboard** → **Workers & Pages**
2. Sélectionnez votre projet **leonie-frontend**
3. Cliquez sur **Settings** → **Environment variables**
4. Trouvez `VITE_API_URL`
5. Cliquez sur **Edit** et remplacez par :
   ```
   https://votre-app-railway.up.railway.app/api
   ```
6. Cliquez sur **Save**
7. Allez dans **Deployments**
8. Cliquez sur **Retry deployment** pour redéployer avec la nouvelle URL

---

## 🎯 Résumé des paramètres

| Paramètre | Valeur |
|-----------|--------|
| **Repo GitHub** | `bahmanarsonVXP/leonie` |
| **Branch** | `main` |
| **Root directory** | `frontend` |
| **Build command** | `npm run build` |
| **Output directory** | `dist` |
| **Framework** | Vite |

### Variables d'environnement

```bash
VITE_SUPABASE_URL=https://wybypzuuyxzgdtmslcko.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_URL=https://[backend-railway].up.railway.app/api
```

---

## 🐛 Troubleshooting

### Build échoue avec "Command not found: npm"

❌ Problème : Node.js non détecté
✅ Solution : Framework preset doit être **Vite**

### Build échoue avec "No such file or directory"

❌ Problème : Root directory incorrecte
✅ Solution : Root directory = `frontend` (pas `./frontend` ou `/frontend`)

### Page blanche après déploiement

❌ Problème : Variables d'environnement manquantes
✅ Solution : Vérifier que les 3 variables `VITE_*` sont définies

### Login ne fonctionne pas

❌ Problème : Backend pas encore déployé ou VITE_API_URL incorrecte
✅ Solution : Déployer le backend sur Railway et mettre à jour `VITE_API_URL`

---

## 🎉 C'est fait !

Votre frontend est maintenant déployé sur Cloudflare Pages !

**Prochaine étape** : Déployer le backend sur Railway pour que tout fonctionne ensemble.
