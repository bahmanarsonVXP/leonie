# 📋 CONTEXT - Projet Léonie

**Dernière mise à jour** : 22 décembre 2024
**Session actuelle** : Session 8 complétée (Frontend + Déploiements)
**Prochaine session** : Session 9 - Agent conversationnel Email First

---

## 🎯 Vue d'ensemble du projet

**Léonie** est un agent IA pour courtiers en prêts immobiliers et professionnels.

### Objectif principal
Automatiser le traitement des emails, la classification des documents et la gestion des dossiers clients via:
- **Agent conversationnel Email First** (prioritaire pour Session 9)
- Interface web de suivi (développement reporté)

### Architecture globale
```
Courtier → Email (Gmail) → Léonie (IA) → Classification → Google Drive
                                        ↓
                              Supabase (BDD) → Frontend (suivi)
```

---

## 📁 Structure du projet (Monorepo)

```
/Users/bahmanarson/projects/leonie/
├── backend/              # API FastAPI + Workers
│   ├── app/             # Code application
│   ├── main.py          # Point d'entrée FastAPI
│   ├── requirements.txt # Dépendances Python
│   ├── Dockerfile       # Image Docker pour Railway
│   └── .env             # Variables locales (NON commité)
├── frontend/            # React + Vite + TypeScript
│   ├── src/            # Code source React
│   ├── .env.production # Variables production (commité)
│   └── package.json    # Dépendances npm
├── CONTEXT.md          # Ce fichier
└── README.md
```

### Git
- **Repository** : `https://github.com/bahmanarsonVXP/leonie`
- **Branch** : `main`
- **Auto-déploiement** :
  - Cloudflare Pages (frontend) : Push sur main
  - Railway (backend) : Via CLI `railway up`

---

## 🌐 Déploiements et URLs

### Backend (Railway)
- **URL Production** : `https://web-production-b71d4.up.railway.app`
- **Health Check** : `https://web-production-b71d4.up.railway.app/health`
- **Status** : ✅ Fonctionnel (retourne "healthy")
- **Projet Railway** : "leonie" (anciennement "endearing-wisdom")
- **Service** : `web`

**Endpoints disponibles :**
- `GET /` - Message de bienvenue
- `GET /health` - Health check avec statut dépendances
- `GET /api/info` - Informations API
- `GET /test-imap` - Test connexion Gmail IMAP
- `POST /test-mistral` - Test classification Mistral AI
- `POST /test-document` - Test traitement documents
- `POST /test-drive` - Test Google Drive
- `GET /cron/check-emails` - Déclencher vérification emails

### Frontend (Cloudflare Pages)
- **URL Temporaire** : `https://leonie-cz6.pages.dev`
- **URL Custom** : `leonie.voxperience.com` (à configurer via CNAME)
- **Status** : ✅ Fonctionnel (login + navigation)
- **Projet** : `leonie-cz6`
- **Branch déploiement** : `main`
- **Root directory** : `frontend`

**Pages implémentées :**
- `/login` - Authentification Supabase
- `/dashboard` - Tableau de bord (squelette)
- `/dossiers` - Liste dossiers (squelette)
- `/dossiers/:id` - Détail dossier (squelette)
- `/admin` - Administration courtiers (squelette)

---

## 🔧 Services et Configurations

### 1. Supabase (Base de données + Auth)

**URL** : `https://wybypzuuyxzgdtmslcko.supabase.co`

**Credentials :**
```bash
SUPABASE_URL=https://wybypzuuyxzgdtmslcko.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind5YnlwenV1eXh6Z2R0bXNsY2tvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU3NzQxNjQsImV4cCI6MjA4MTM1MDE2NH0.duIB8Eqe--DH-6V5W-77B8u00NcByqm6_vLJ7MtDs08
SUPABASE_JWT_SECRET=2p76jtoVmV6lHNZGPugccaZiUUmhrE/TvaDjQNu24j7NiZYgX2bo5OtP3SRGbAZ+vf8RNfs9Opt9RLSyJusvHA==
```

**Tables principales :**
- `courtiers` - Courtiers (utilisateurs)
- `clients` - Clients des courtiers
- `dossiers` - Dossiers de prêt
- `pieces` - Pièces/documents par dossier
- `activites` - Timeline des événements

**Schema** : Voir `backend/schema.sql`

### 2. Gmail IMAP/SMTP

**Email principal** : `leonie@voxperience.com`

**Configuration IMAP :**
```bash
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_EMAIL=leonie@voxperience.com
IMAP_PASSWORD=[App Password Gmail]
IMAP_LABEL=LEONIE
EMAIL_POLLING_INTERVAL=300
```

**Configuration SMTP :**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=leonie@voxperience.com
SMTP_PASSWORD=[App Password Gmail]
SMTP_FROM_NAME=Léonie
```

**Workflow emails :**
1. Courtier forward email → `leonie@voxperience.com`
2. Gmail applique label `LEONIE`
3. Backend lit IMAP toutes les 5 min
4. Mistral AI classifie l'email
5. Actions automatiques selon classification

### 3. Mistral AI

**API Key** : `NsLsIAd7VFfqxDTQRXrIOjVNSwNVIEa8`

**Configuration :**
```bash
MISTRAL_API_KEY=NsLsIAd7VFfqxDTQRXrIOjVNSwNVIEa8
MISTRAL_MODEL_CHAT=mistral-large-latest
MISTRAL_MODEL_VISION=pixtral-large-latest
MISTRAL_MAX_TOKENS=2000
MISTRAL_TEMPERATURE=0.1
```

**Usages :**
- Classification des emails (nouveau dossier, ajout pièce, modification liste, autre)
- Extraction d'informations (nom client, type de prêt, etc.)
- Analyse de documents avec vision (pixtral)

### 4. Google Drive

**Service Account** : `leonie-drive@leoniedrive.iam.gserviceaccount.com`
**Master Folder ID** : `0ANXBJHaSDohtUk9PVA`

**Configuration :**
```bash
GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"leoniedrive",...}'
GOOGLE_DRIVE_MASTER_FOLDER_ID=0ANXBJHaSDohtUk9PVA
```

**Structure Drive :**
```
DOSSIERS_PRETS/
├── Courtier_NOM_PRENOM/
│   ├── Client_NOM_PRENOM/
│   │   ├── Pièce1.pdf
│   │   ├── Pièce2.pdf
│   │   └── ...
```

**Fonctionnalités :**
- Création automatique dossiers courtier/client
- Upload documents avec compression PDF
- Génération liens partageables
- Vérification existence fichiers (hash SHA256)

### 5. Redis (Workers - NON installé en production)

**Status** : ⚠️ **Redis n'est PAS déployé sur Railway**

**Configuration actuelle :**
```bash
REDIS_URL=redis://localhost:6379/0  # Local uniquement
```

**Décision technique :**
- Redis est **optionnel** pour l'API principale
- Nécessaire seulement pour les workers/jobs en arrière-plan
- API démarre sans Redis (workers désactivés)
- À installer sur Railway si besoin de traitement asynchrone

**Code à modifier si Redis activé :**
- `app/config.py` : Rendre REDIS_URL optionnel
- `main.py:179` : Vérifier vraiment Redis au lieu de hardcode `"redis":"ok"`

---

## 🛠️ Stack Technique

### Backend
- **Framework** : FastAPI (Python 3.11)
- **ORM/Client** : Supabase Python SDK
- **Email** : imaplib (IMAP), smtplib (SMTP)
- **IA** : Mistral AI SDK
- **Documents** :
  - LibreOffice (conversion Office → PDF)
  - Ghostscript (compression PDF)
  - Poppler (extraction texte PDF)
  - Pillow (traitement images)
- **Storage** : Google Drive API v3
- **Logging** : structlog
- **Déploiement** : Docker (Railway)

### Frontend
- **Framework** : React 18 + TypeScript
- **Build** : Vite 7.3.0
- **Routing** : React Router v6
- **Auth** : Supabase Auth (@supabase/supabase-js)
- **HTTP** : Fetch API native
- **UI** : Capital In Fine Design System
- **CSS** : Tailwind CSS v3.4.19
- **Icons** : lucide-react
- **Déploiement** : Cloudflare Pages

---

## ✅ Ce qui fonctionne actuellement

### Backend (Railway)
- ✅ API FastAPI opérationnelle
- ✅ Health check retourne toutes les dépendances OK
- ✅ Connexion Supabase
- ✅ Connexion Gmail IMAP/SMTP
- ✅ Mistral AI classification
- ✅ Google Drive upload/création dossiers
- ✅ Traitement documents (PDF, images, Office)
- ✅ Endpoints de test disponibles

### Frontend (Cloudflare)
- ✅ Build Vite avec variables d'environnement
- ✅ Authentification Supabase fonctionnelle
- ✅ Login/Logout
- ✅ Routes protégées
- ✅ Navigation (Sidebar + Header)
- ✅ Design Capital In Fine appliqué

### Déploiements
- ✅ Auto-deploy Cloudflare (push GitHub)
- ✅ Deploy Railway via CLI (`railway up`)
- ✅ SSL/HTTPS sur les deux environnements
- ✅ Variables d'environnement configurées

---

## 🚧 Ce qui reste à faire

### Session 9 : Agent conversationnel Email First (PRIORITÉ)

**Objectif** : Construire un agent IA qui répond aux emails des courtiers

**Fonctionnalités à implémenter :**
1. **Lecture emails** :
   - Polling IMAP automatique (déjà partiellement fait)
   - Classification Mistral AI (déjà fait)

2. **Génération réponses** :
   - Réponses contextuelles selon type d'email
   - Confirmation création dossier
   - Demande informations manquantes
   - Notification pièces reçues

3. **Envoi réponses** :
   - SMTP vers courtier
   - Thread/Reply-To pour conserver contexte
   - Format email professionnel

4. **Actions automatiques** :
   - Création dossier Drive
   - Upload documents
   - Mise à jour Supabase
   - Notifications

**Fichiers à modifier/créer :**
- `backend/app/cron/check_emails.py` - Améliorer traitement emails
- `backend/app/services/email_agent.py` - Nouveau: Agent conversationnel
- `backend/app/services/smtp.py` - Nouveau: Envoi emails
- `backend/app/services/response_generator.py` - Nouveau: Génération réponses IA

### Sessions futures (reportées)

**Session 10 : Dashboard Frontend**
- Statistiques temps réel
- Liste dossiers avec données API
- Graphiques progression
- Tableaux triables/filtrables

**Session 11 : Détail Dossier**
- Page détail complète
- Liste pièces avec statuts
- Upload manuel documents
- Actions (rapport, marquer complet)
- Timeline activités

**Session 12 : Interface Admin**
- CRUD courtiers
- Gestion permissions
- Statistiques globales

---

## 📝 Décisions techniques importantes

### 1. Monorepo GitHub + Déploiements séparés
- **Choix** : Un seul repo, deux dossiers (backend/, frontend/)
- **Raison** : Simplicité, pas besoin de Turborepo/Nx
- **Déploiements** :
  - Cloudflare lit `frontend/` uniquement
  - Railway déploie depuis CLI (pas GitHub)

### 2. Variables d'environnement Vite
- **Problème** : Cloudflare ne voyait pas les variables
- **Solution** : Créer `.env.production` commité dans Git
- **Fichier** : `frontend/.env.production`
- **Contenu** : Variables `VITE_*` publiques (safe)

### 3. Redis optionnel
- **Problème** : Backend crashait sans Redis
- **Décision** : Rendre Redis optionnel
- **Status** : API fonctionne sans Redis, workers désactivés
- **À faire** : Si besoin workers, ajouter Redis sur Railway

### 4. TypeScript strict mode
- **Problème** : Erreurs compilation avec project references
- **Solution** :
  - `tsconfig.node.json` : Ajout `composite: true`
  - Suppression `noEmit` incompatible avec `composite`
  - Ajout `emitDeclarationOnly: true`

### 5. Tailwind CSS v3 vs v4
- **Problème** : Tailwind v4 incompatible avec PostCSS existant
- **Solution** : Downgrade vers Tailwind CSS v3.4.19
- **Commande** : `npm install -D tailwindcss@^3.4.0`

---

## 🔑 Credentials et Secrets

### Locaux (développement)
- **Backend** : `/Users/bahmanarson/projects/leonie/backend/.env`
- **Frontend** : `/Users/bahmanarson/projects/leonie/frontend/.env.local`

### Production
- **Railway** : Variables configurées via Dashboard ou CLI
- **Cloudflare** : Variables dans `.env.production` (commité)

**⚠️ Fichiers à NE JAMAIS committer :**
- `backend/.env`
- `frontend/.env.local`
- Tout fichier contenant des secrets (service-account.json, etc.)

---

## 🐛 Problèmes résolus

### 1. Backend 502 sur Railway
- **Cause** : Variable `SUPABASE_JWT_SECRET` manquante
- **Solution** : Ajout via `railway variables --set`

### 2. Frontend écran blanc Cloudflare
- **Cause** : Variables `VITE_*` non injectées au build
- **Solution** : Créer `.env.production` commité

### 3. TypeScript build errors
- **Cause** : Project references mal configurées
- **Solution** : Ajout `composite: true` + `emitDeclarationOnly`

### 4. Port 8000 déjà utilisé localement
- **Cause** : Process en arrière-plan
- **Solution** : Script `start.sh` nettoie les ports automatiquement

---

## 📚 Documentation importante

### Backend
- `backend/README.md` - Documentation backend
- `backend/DEPLOY_RAILWAY.md` - Guide déploiement Railway
- `backend/GOOGLE-DRIVE-SETUP.md` - Configuration Google Drive
- `backend/schema.sql` - Schema Supabase complet

### Frontend
- `frontend/README.md` - Documentation frontend
- `CLOUDFLARE_CLI_DEPLOYMENT.md` - Déploiement CLI Cloudflare
- `CLOUDFLARE_DEPLOYMENT.md` - Déploiement Dashboard Cloudflare

### Général
- `README.md` - Vue d'ensemble projet
- `CONTEXT.md` - Ce fichier

---

## 🚀 Commandes utiles

### Développement local

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm run dev

# Démarrage complet (backend + frontend)
./start.sh
```

### Déploiement

```bash
# Backend Railway
cd backend
railway up

# Frontend Cloudflare (auto via GitHub)
git add .
git commit -m "feat: nouvelle feature"
git push origin main

# Vérification
railway status
railway logs
```

### Tests

```bash
# Backend endpoints
curl https://web-production-b71d4.up.railway.app/health
curl https://web-production-b71d4.up.railway.app/test-imap

# Frontend
open https://leonie-cz6.pages.dev
```

---

## 👤 Contacts et Ressources

### Domaines
- **Principal** : `voxperience.com` (géré par IONOS)
- **Custom domain** : `leonie.voxperience.com` (à configurer)

### Services externes
- **Supabase** : https://supabase.com/dashboard
- **Railway** : https://railway.app/
- **Cloudflare** : https://dash.cloudflare.com/
- **Google Cloud** : https://console.cloud.google.com/
- **Mistral AI** : https://console.mistral.ai/

### Support
- **GitHub Issues** : `https://github.com/bahmanarsonVXP/leonie/issues`
- **Email** : `leonie@voxperience.com`

---

## 📊 Métriques actuelles

**Tokens utilisés Session 8** : ~88k / 200k
**Fichiers backend** : ~71 fichiers Python
**Fichiers frontend** : ~40 composants React
**Lignes de code backend** : ~15k lignes
**Lignes de code frontend** : ~3k lignes

**État global** : ✅ Infrastructure déployée et fonctionnelle

---

## 🎯 Prochaine session

**Focus** : Agent conversationnel Email First (Session 9)

**Contexte à donner :**
> "Session 9 : Nous avons un backend FastAPI déployé sur Railway qui peut lire les emails Gmail, classifier avec Mistral AI, et stocker dans Supabase + Google Drive. L'objectif est de créer un agent conversationnel qui répond automatiquement aux emails des courtiers de manière intelligente et contextuelle."

**Fichier contexte à joindre** : `/Users/bahmanarson/projects/leonie/CONTEXT.md`

---

**Fin du contexte - Mise à jour : 22 décembre 2024**
