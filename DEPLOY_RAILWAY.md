# Guide de Déploiement Railway

## 📋 Vue d'ensemble

Ce guide explique comment déployer Léonie sur Railway.app.

## 🔍 Problème actuel : Worker en erreur

Le service `# worker` crash car :
- Il essaie de se connecter à Redis sur `localhost:6379`
- Redis n'est pas disponible sur Railway (pas encore configuré)
- Le worker n'est **pas encore utilisé** dans l'application

## ✅ Solution immédiate : Désactiver le worker

Le worker est déjà commenté dans le `Procfile`, mais Railway peut l'avoir détecté automatiquement.

### Option 1 : Supprimer le service worker sur Railway (RECOMMANDÉ)

1. Aller sur votre projet Railway
2. Dans la vue "Architecture", cliquer sur le service `# worker`
3. Aller dans "Settings"
4. Cliquer sur "Delete Service" ou "Remove"

### Option 2 : S'assurer que le Procfile est correct

Le `Procfile` doit contenir uniquement :
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Le worker doit rester commenté :
```
# worker: rq worker high default --with-scheduler
```

## 🚀 Déploiement complet sur Railway

### 1. Prérequis

- Compte Railway créé
- Repository GitHub connecté
- Variables d'environnement prêtes

### 2. Créer le projet Railway

1. Aller sur [railway.app](https://railway.app)
2. Cliquer sur **"New Project"**
3. Sélectionner **"Deploy from GitHub repo"**
4. Choisir le repository `bahmanarsonVXP/leonie`
5. Railway détecte automatiquement le `Procfile` et crée le service `web`

### 3. Configurer les variables d'environnement

Dans Railway, aller dans **Variables** et ajouter :

#### Variables obligatoires

```bash
# Supabase
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre-clé-supabase

# Gmail IMAP
IMAP_HOST=imap.gmail.com
IMAP_EMAIL=leonie.capitalinfinie@gmail.com
IMAP_PASSWORD=votre-mot-de-passe-application
IMAP_LABEL=INBOX

# Mistral AI
MISTRAL_API_KEY=votre-clé-mistral

# Environnement
ENVIRONMENT=production
PORT=${{PORT}}  # Railway le définit automatiquement
```

#### Variables optionnelles

```bash
# Redis (pour plus tard, quand les workers seront implémentés)
# REDIS_URL=redis://default:password@redis.railway.app:6379

# Google Drive (si utilisé)
# GOOGLE_DRIVE_FOLDER_ID=votre-folder-id
```

### 4. Vérifier le déploiement

1. Attendre que le déploiement se termine (icône verte)
2. Vérifier les logs : pas d'erreurs
3. Tester l'endpoint de santé :
   ```bash
   curl https://votre-app.railway.app/health
   ```

### 5. Obtenir l'URL publique

1. Dans Railway, aller dans **Settings** du service `web`
2. Activer **"Generate Domain"** si ce n'est pas déjà fait
3. L'URL sera : `https://votre-app.up.railway.app`

## 🔧 Configuration avancée (pour plus tard)

### Ajouter Redis (quand les workers seront implémentés)

1. Dans Railway, cliquer sur **"+ New"** → **"Database"** → **"Add Redis"**
2. Railway crée automatiquement une variable `REDIS_URL`
3. Décommenter le worker dans le `Procfile` :
   ```
   worker: rq worker high default --with-scheduler
   ```
4. Railway détectera automatiquement le nouveau service

### Variables d'environnement Railway

Railway peut utiliser des variables d'environnement de plusieurs façons :

1. **Variables du projet** : Partagées entre tous les services
2. **Variables du service** : Spécifiques à un service
3. **Variables de référence** : `${{REDIS.REDIS_URL}}` pour référencer un service

## 🐛 Dépannage

### Le service `web` ne démarre pas

- Vérifier les logs dans Railway
- Vérifier que toutes les variables d'environnement sont définies
- Vérifier que `PORT` est bien défini (Railway le fait automatiquement)

### Erreur de connexion à Supabase

- Vérifier `SUPABASE_URL` et `SUPABASE_KEY`
- Vérifier que les tables existent dans Supabase

### Erreur de connexion IMAP

- Vérifier `IMAP_EMAIL` et `IMAP_PASSWORD`
- S'assurer d'utiliser un "App Password" Gmail, pas le mot de passe normal

### Le worker crash

- **Solution immédiate** : Supprimer le service worker (il n'est pas encore utilisé)
- **Pour plus tard** : Ajouter Redis et configurer `REDIS_URL`

## 📝 Notes importantes

- Le service `web` est le seul nécessaire pour l'instant
- Le worker sera activé plus tard quand les jobs asynchrones seront implémentés
- Railway déploie automatiquement à chaque push sur la branche principale
- Les variables d'environnement sont sécurisées et chiffrées sur Railway

## 🔗 Ressources

- [Documentation Railway](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)

