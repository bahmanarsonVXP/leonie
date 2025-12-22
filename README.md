# Léonie - Monorepo

Agent IA de gestion de dossiers de prêt pour courtiers.

## 🏗️ Architecture Monorepo

```
leonie/
├── backend/          # API FastAPI (Python)
├── frontend/         # Interface React (TypeScript)
├── start.sh          # Script de démarrage rapide
├── docker-compose.yml
└── README.md         # Ce fichier
```

---

## 🚀 Démarrage Rapide (Local)

### Option 1 : Script automatique (Recommandé)

```bash
./start.sh
```

Ce script lance automatiquement :
- ✅ Backend FastAPI sur `http://localhost:8000`
- ✅ Frontend React sur `http://localhost:3000`
- ✅ Redis (si installé)

**Arrêter les serveurs** : `Ctrl+C` dans le terminal

### Option 2 : Manuel (2 terminaux)

**Terminal 1 - Backend** :
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
# → http://localhost:8000
```

**Terminal 2 - Frontend** :
```bash
cd frontend
npm run dev
# → http://localhost:3000
```

### Option 3 : Docker Compose

```bash
docker-compose up
```

---

## 📦 Installation Initiale

### Backend (Python)

```bash
cd backend

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt

# Configurer .env
cp .env.example .env
# Éditer .env avec vos credentials

# Lancer Redis (requis)
redis-server

# Tester
uvicorn main:app --reload
```

**Backend accessible sur** : `http://localhost:8000`
**Documentation API** : `http://localhost:8000/docs`

### Frontend (React)

```bash
cd frontend

# Installer dépendances
npm install

# Configurer .env.local
cp .env.example .env.local
# Éditer .env.local avec vos credentials Supabase

# Tester
npm run dev
```

**Frontend accessible sur** : `http://localhost:3000`

---

## 🌐 Déploiement

### Backend → Railway

**Configuration Railway** :
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Fichier de config** : `backend/railway.toml`

**Variables d'environnement** :
Copier toutes les variables de `backend/.env.example` dans Railway Dashboard.

### Frontend → Cloudflare Pages

**Configuration Cloudflare Pages** :
- Root directory: `frontend`
- Framework preset: **Vite**
- Build command: `npm run build`
- Build output directory: `dist`

**Variables d'environnement** :
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_URL` (URL Railway backend)

---

## 🔐 Configuration

### Backend `.env`

Variables essentielles (voir `backend/.env.example` pour la liste complète) :

```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
SUPABASE_JWT_SECRET=xxx

# Redis
REDIS_URL=redis://localhost:6379/0

# Email IMAP
IMAP_EMAIL=leonie@voxperience.com
IMAP_PASSWORD=xxx

# Mistral AI
MISTRAL_API_KEY=xxx

# Google Drive
GOOGLE_CREDENTIALS_JSON='{"type":"service_account",...}'
GOOGLE_DRIVE_MASTER_FOLDER_ID=xxx

# Admin
ADMIN_EMAIL=admin@voxperience.com
```

### Frontend `.env.local`

```bash
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=xxx
VITE_API_URL=http://localhost:8000/api
```

---

## 📚 Documentation

- **Backend** : Voir `backend/README.md`
- **Frontend** : Voir `frontend/README.md`
- **API Docs** : `http://localhost:8000/docs`

---

## 🧪 Tests

### Backend

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm run test
```

---

## 🛠️ Développement

### Structure des projets

**Backend** (`backend/`) :
```
backend/
├── app/
│   ├── api/              # Endpoints REST
│   ├── services/         # Logique métier
│   ├── workers/          # Jobs background
│   ├── middleware/       # Auth JWT
│   └── utils/            # Helpers
├── main.py               # Point d'entrée
└── requirements.txt
```

**Frontend** (`frontend/`) :
```
frontend/
├── src/
│   ├── components/       # Composants React
│   ├── pages/            # Pages
│   ├── services/         # API calls
│   ├── contexts/         # React contexts
│   └── types/            # TypeScript types
└── package.json
```

### Workflow Git

```bash
# Créer une branche
git checkout -b feature/ma-feature

# Travailler...
git add .
git commit -m "feat: ma feature"

# Push
git push origin feature/ma-feature

# Créer PR sur GitHub
```

### Auto-déploiement

Cloudflare et Railway déploient automatiquement depuis GitHub :
- **Backend** : Changements dans `backend/` → Deploy Railway
- **Frontend** : Changements dans `frontend/` → Deploy Cloudflare

---

## 🔄 Workflow Complet

### 1. Développement Local

```bash
# Lancer les serveurs
./start.sh

# Backend : http://localhost:8000
# Frontend : http://localhost:3000
# Docs API : http://localhost:8000/docs
```

### 2. Tester

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm run test
```

### 3. Commit & Push

```bash
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push origin main
```

### 4. Déploiement Automatique

- ✅ Railway build et déploie backend
- ✅ Cloudflare build et déploie frontend

---

## 📋 Sessions Implémentées

- ✅ **Session 1-7** : Backend complet (API, Auth, Workers, Reports)
- ✅ **Session 8** : Frontend setup (Auth, Routing, Layout)
- ⏳ **Session 9** : Dashboard complet
- ⏳ **Session 10** : Page détail dossier
- ⏳ **Session 11** : Interface admin

---

## 🐛 Troubleshooting

### Backend ne démarre pas

```bash
# Vérifier Python
python --version  # 3.11+

# Vérifier venv activé
which python  # Doit pointer vers venv/

# Vérifier Redis
redis-cli ping  # Doit retourner PONG

# Vérifier .env
cat backend/.env | grep SUPABASE_URL
```

### Frontend ne démarre pas

```bash
# Vérifier Node
node --version  # 18+

# Nettoyer et réinstaller
rm -rf node_modules package-lock.json
npm install

# Vérifier .env.local
cat frontend/.env.local | grep VITE_
```

### Erreurs CORS

Vérifier que le frontend appelle le bon backend :
- Local : `http://localhost:8000/api`
- Prod : URL Railway dans `.env.local`

---

## 📞 Support

Pour toute question :
- Backend : Voir documentation dans `backend/README.md`
- Frontend : Voir documentation dans `frontend/README.md`
- Issues : Créer une issue GitHub

---

## 📄 License

Propriétaire - Voxperience © 2024
