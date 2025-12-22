# Léonie - Agent IA pour Courtiers

Agent IA intelligent pour courtiers en prêts immobiliers et professionnels. Léonie automatise la réception, la classification et l'organisation des documents clients via email.

## Architecture

- **Backend**: Python FastAPI
- **Base de données**: Supabase (PostgreSQL)
- **Queue**: Redis + RQ (Redis Queue)
- **Stockage**: Google Drive
- **IA**: Mistral AI (classification documents)
- **Email**: IMAP Gmail (polling)
- **Déploiement**: Railway

## Fonctionnalités

- Réception automatique d'emails via IMAP Gmail
- Classification intelligente des pièces justificatives avec Mistral AI
- Stockage organisé sur Google Drive
- Détection de doublons
- Rapports quotidiens pour les courtiers
- API REST pour consultation des dossiers
- Gestion multi-courtiers avec isolation des données (RLS)

---

## Installation Locale

### Prérequis

- Python 3.11+
- Redis (local ou distant)
- Compte Supabase
- Compte Google Cloud (pour Drive API)
- Compte Mistral AI
- Compte Gmail avec alias

### 1. Cloner le projet

```bash
git clone <votre-repo>
cd leonie-backend
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

**Dépendances système supplémentaires** :

```bash
# macOS
brew install poppler tesseract redis

# Ubuntu/Debian
sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-fra redis-server

# Windows: télécharger manuellement
# Poppler: https://github.com/oschwartz10612/poppler-windows
# Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
```

### 4. Configuration Supabase

1. Créer un projet sur [supabase.com](https://supabase.com)
2. Aller dans l'éditeur SQL
3. Exécuter le contenu de `schema.sql`
4. Récupérer les clés API dans **Project Settings > API**

### 5. Configuration Google Drive

1. Créer un projet sur [Google Cloud Console](https://console.cloud.google.com)
2. Activer **Google Drive API**
3. Créer un **Service Account**
4. Télécharger le fichier JSON des credentials
5. Placer le fichier dans le projet (ex: `service-account.json`)
6. Partager les dossiers Drive avec l'email du Service Account

### 6. Configuration Gmail

1. Créer un alias Gmail (ex: `leonie@voxperience.com`)
2. Activer **l'authentification à 2 facteurs**
3. Créer un **App Password** dans **Compte Google > Sécurité**
4. Noter le mot de passe généré (format: `xxxx xxxx xxxx xxxx`)

### 7. Configuration Mistral AI

1. Créer un compte sur [console.mistral.ai](https://console.mistral.ai)
2. Générer une clé API
3. Noter la clé API

### 8. Configuration Redis (local)

```bash
# Démarrer Redis
redis-server

# Vérifier que Redis fonctionne
redis-cli ping
# Devrait retourner: PONG
```

### 9. Variables d'environnement

```bash
# Copier le template
cp .env.example .env

# Éditer .env avec vos vraies valeurs
nano .env  # ou votre éditeur préféré
```

**Variables obligatoires à remplir** :

```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Gmail IMAP
IMAP_EMAIL=leonie@voxperience.com
IMAP_PASSWORD=xxxx xxxx xxxx xxxx

# Gmail SMTP
SMTP_EMAIL=leonie@voxperience.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx

# Mistral AI
MISTRAL_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Drive
GOOGLE_CREDENTIALS_FILE=service-account.json

# Sécurité
API_SECRET_KEY=<générer avec: openssl rand -hex 32>
```

### 10. Lancer l'application

```bash
# Mode développement avec reload
uvicorn main:app --reload --port 8000

# Ou directement
python main.py
```

L'API sera accessible sur : http://localhost:8000

- **Documentation** : http://localhost:8000/docs
- **Health Check** : http://localhost:8000/health

### 11. Lancer le worker Redis Queue (optionnel pour l'instant)

Dans un terminal séparé :

```bash
rq worker high default --with-scheduler
```

---

## Déploiement Railway

### 1. Créer un projet Railway

1. Aller sur [railway.app](https://railway.app)
2. Créer un nouveau projet
3. Connecter votre repository GitHub

### 2. Ajouter un service Redis

1. Dans Railway, cliquer sur **New Service**
2. Sélectionner **Redis**
3. Noter l'URL de connexion Redis

### 3. Variables d'environnement Railway

Ajouter toutes les variables du fichier `.env` dans Railway :

- Aller dans **Variables**
- Ajouter une par une les variables
- Pour `REDIS_URL`, utiliser l'URL fournie par Railway
- Définir `ENVIRONMENT=production`
- Définir `PORT` (Railway le fait automatiquement)

### 4. Déployer

Railway déploie automatiquement à chaque push sur la branche principale.

Vérifier le déploiement :
```bash
curl https://votre-app.railway.app/health
```

---

## Structure du Projet

```
leonie-backend/
├── main.py                    # Point d'entrée FastAPI
├── requirements.txt           # Dépendances Python
├── .env.example              # Template variables d'env
├── .gitignore                # Git ignore
├── Procfile                  # Railway deployment
├── README.md                 # Cette documentation
├── schema.sql                # Schema Supabase
│
├── app/
│   ├── __init__.py
│   ├── config.py             # Settings (pydantic-settings)
│   │
│   ├── api/                  # Endpoints API
│   │   ├── webhook.py        # POST /webhook/email (IMAP)
│   │   ├── dossiers.py       # GET /api/dossiers
│   │   ├── admin.py          # CRUD courtiers (admin)
│   │   └── cron.py           # GET /cron/daily-report
│   │
│   ├── services/             # Services métier
│   │   ├── email_fetcher.py  # IMAP Gmail
│   │   ├── email_parser.py   # Parse emails
│   │   ├── mistral.py        # Mistral API
│   │   ├── document.py       # PDF processing
│   │   ├── drive.py          # Google Drive
│   │   ├── report.py         # Rapports Word
│   │   └── notification.py   # Send emails
│   │
│   ├── models/               # Modèles Pydantic v2
│   │   ├── courtier.py
│   │   ├── client.py
│   │   ├── piece.py
│   │   └── email.py
│   │
│   ├── workers/              # Redis Queue jobs
│   │   └── jobs.py
│   │
│   └── utils/                # Utilitaires
│       ├── db.py             # Supabase client
│       └── redis.py          # Redis connection
│
└── tests/
    └── fixtures/
```

---

## Base de Données

### Tables principales

- **courtiers** : Courtiers utilisant le système
- **clients** : Dossiers clients des courtiers
- **types_pieces** : Catalogue des types de pièces justificatives
- **pieces_dossier** : Pièces reçues dans les dossiers
- **config** : Configuration globale
- **logs_activite** : Journal d'activité

### Row Level Security (RLS)

Les données sont isolées par courtier grâce aux policies RLS :
- Un courtier ne voit que ses propres clients
- Un admin peut tout voir

---

## API Endpoints (à venir)

### Health & Info
- `GET /` - Message de bienvenue
- `GET /health` - Health check
- `GET /api/info` - Informations API

### Webhook (Session 2+)
- `POST /webhook/email` - Traiter un email reçu

### Dossiers (Session 3+)
- `GET /api/dossiers` - Liste des dossiers
- `GET /api/dossiers/{id}` - Détails d'un dossier
- `GET /api/dossiers/{id}/pieces` - Pièces d'un dossier

### Admin (Session 4+)
- `POST /api/admin/courtiers` - Créer un courtier
- `GET /api/admin/courtiers` - Liste des courtiers
- `PUT /api/admin/courtiers/{id}` - Modifier un courtier

### Cron (Session 5+)
- `GET /cron/daily-report` - Rapport quotidien

---

## Développement

### Tests

```bash
# Lancer les tests
pytest

# Avec coverage
pytest --cov=app --cov-report=html
```

### Linting & Formatting

```bash
# Formatter le code
black .
isort .

# Linter
flake8
pylint app/
```

### Type Checking

```bash
mypy app/
```

---

## Tester IMAP

### Configuration initiale

Avant de tester IMAP, assurez-vous que vos variables d'environnement sont correctement configurées dans `.env` :

```env
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_EMAIL=leonie@voxperience.com
IMAP_PASSWORD=xxxx xxxx xxxx xxxx  # App Password Gmail
IMAP_FOLDER=INBOX
```

**Important** : Pour Gmail, vous devez utiliser un **App Password** et non votre mot de passe principal.

### 1. Créer un App Password Gmail

1. Aller dans **Compte Google > Sécurité**
2. Activer **l'authentification à 2 facteurs** (obligatoire)
3. Cliquer sur **Mots de passe des applications**
4. Sélectionner **Autre** et nommer "Léonie"
5. Copier le mot de passe généré (format: `xxxx xxxx xxxx xxxx`)
6. Coller dans `.env` comme valeur de `IMAP_PASSWORD`

### 2. Test de connexion IMAP

Démarrez l'application :

```bash
python main.py
```

Testez la connexion IMAP via l'endpoint de test :

```bash
# Test de connexion
curl http://localhost:8000/test-imap

# Ou dans votre navigateur
open http://localhost:8000/test-imap
```

**Résultat attendu** :

```json
{
  "status": "success",
  "connected": true,
  "imap_server": "imap.gmail.com",
  "imap_user": "leonie@voxperience.com",
  "folder": "INBOX",
  "total_emails": 42,
  "unseen_emails": 5
}
```

### 3. Vérification manuelle des emails

Pour tester la récupération et le parsing des emails :

```bash
# Déclencher manuellement la vérification
curl http://localhost:8000/cron/check-emails

# Ou dans votre navigateur
open http://localhost:8000/cron/check-emails
```

**Résultat attendu** :

```json
{
  "total_emails": 3,
  "nouveaux_dossiers": 1,
  "emails_avec_pieces_jointes": 2,
  "courtiers_identifies": 3,
  "clients_identifies": 2,
  "erreurs": 0
}
```

Consultez les logs pour voir les détails du traitement :

```bash
# Les logs s'affichent dans le terminal où tourne l'application
# Vous verrez pour chaque email :
# - Expéditeur, destinataires, sujet
# - Détection nouveau dossier
# - Nombre de pièces jointes
# - Identification courtier/client
```

### 4. Tests unitaires

Lancer les tests du fetcher IMAP :

```bash
# Tous les tests
pytest tests/test_email_fetcher.py -v

# Test spécifique
pytest tests/test_email_fetcher.py::TestEmailFetcher::test_connect_success -v

# Avec coverage
pytest tests/test_email_fetcher.py --cov=app.services.email_fetcher --cov-report=html
```

### 5. Envoyer un email de test

Pour tester le flux complet, envoyez un email à `leonie@voxperience.com` avec :

**Sujet** : Nouveau dossier prêt immobilier

**Corps** :
```
Bonjour,

Voici le nouveau dossier pour mon client Sophie Martin.

Cordialement,
Jean Dupont (courtier)
```

**CC** : `leonie@voxperience.com`

**Pièces jointes** : 1-2 PDFs de test

Puis vérifiez :

```bash
# 1. Vérifier que l'email est bien reçu
curl http://localhost:8000/test-imap

# 2. Récupérer l'email
curl http://localhost:8000/cron/check-emails

# 3. Consulter les logs
# Vous devriez voir :
# ✅ Courtier identifié
# 🆕 Email détecté comme NOUVEAU DOSSIER
# 📎 2 pièces jointes
```

### 6. Webhook de test

L'endpoint webhook est disponible mais basique pour l'instant :

```bash
# Test du webhook
curl -X POST http://localhost:8000/webhook/email \
  -H "Content-Type: application/json" \
  -d '{}'

# Réponse attendue
{
  "status": "ok",
  "message": "Webhook email reçu et traité"
}
```

### Troubleshooting

#### Erreur "Authentification IMAP échouée"

- Vérifiez que vous utilisez un **App Password** et non votre mot de passe Google
- Vérifiez que l'authentification à 2 facteurs est activée
- Vérifiez que `IMAP_EMAIL` correspond bien à votre compte Gmail

#### Erreur "Impossible de sélectionner le dossier"

- Le dossier `IMAP_FOLDER` dans `.env` doit exister dans votre Gmail
- Utilisez `INBOX` par défaut
- Pour un label personnalisé, utilisez le nom exact (ex: `Leonie`)

#### Aucun email trouvé

- Vérifiez qu'il y a des emails **non lus** dans le dossier
- L'endpoint `/test-imap` vous indique le nombre d'emails non lus
- Marquez des emails comme non lus pour tester

#### Courtier non identifié

- Le courtier doit exister dans la table `courtiers` de Supabase
- L'email expéditeur doit correspondre au champ `email` du courtier
- Créez un courtier de test dans Supabase :

```sql
INSERT INTO courtiers (email, nom, prenom, dossier_drive_id, actif)
VALUES ('courtier@exemple.fr', 'Dupont', 'Jean', 'fake-drive-id', true);
```

---

## Roadmap Sessions

### Session 1/11 ✅
- [x] Structure du projet
- [x] Schéma de base de données
- [x] Modèles Pydantic v2
- [x] Configuration
- [x] FastAPI basique

### Session 2/11 ✅ (Actuelle)
- [x] Service email_fetcher.py (IMAP)
- [x] Service email_parser.py
- [x] API webhook.py
- [x] Fonction cron check_emails.py
- [x] Endpoints de test (/test-imap, /cron/check-emails)
- [x] Tests unitaires

### Session 3/11 (À venir)
- [ ] Service mistral.py (classification)
- [ ] Service document.py (PDF processing)
- [ ] Logique métier traitement pièces

### Sessions 4-11 (À venir)
- Google Drive integration
- Rapports Word
- Notifications courtiers
- Workers RQ
- Admin API
- Frontend dashboard
- Monitoring & logs
- Documentation complète

---

## Support

Pour toute question ou problème :
1. Vérifier les logs : `tail -f logs/leonie.log`
2. Vérifier les variables d'environnement
3. Vérifier les connexions (Supabase, Redis, Gmail)

---

## Licence

Projet privé - Tous droits réservés

---

**Version actuelle** : 0.2.0
**Dernière mise à jour** : Session 2/11 - Email Fetcher IMAP & Parser
