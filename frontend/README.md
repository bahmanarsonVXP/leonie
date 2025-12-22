# Léonie Frontend

Interface web React pour Léonie - Agent IA de gestion de dossiers de prêt.

## 🏗️ Stack Technique

- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **Routing**: React Router v6
- **Auth**: Supabase Auth
- **API**: Axios
- **Styling**: Tailwind CSS + Capital In Fine Design System
- **UI Components**: Radix UI

## 📁 Structure du Projet

```
leonie-frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Composants Capital In Fine (à fournir)
│   │   ├── auth/            # Auth (Login, ProtectedRoute)
│   │   └── layout/          # Layout (Header, Sidebar, Layout)
│   ├── pages/               # Pages (Dashboard, Dossiers, Admin)
│   ├── services/            # API services (auth, dossiers, admin)
│   ├── contexts/            # React contexts (AuthContext)
│   ├── types/               # TypeScript types
│   └── lib/                 # Utilitaires
├── .env.local               # Variables d'environnement (à compléter)
└── .env.example             # Template variables d'environnement
```

## 🚀 Installation

### 1. Installer les dépendances

```bash
npm install
```

### 2. Configurer les variables d'environnement

Créer `.env.local` à la racine du projet :

```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
VITE_API_URL=http://localhost:8000/api
```

Obtenir les credentials Supabase :
- Dashboard Supabase → Settings → API
- Copier `Project URL` et `anon public` key

### 3. Intégrer le Design System Capital In Fine

**IMPORTANT**: Remplacer les fichiers suivants par ceux fournis :

```bash
# Fichiers à remplacer :
- tailwind.config.js      # Configuration Tailwind CIF
- src/index.css           # Styles globaux CIF
- tsconfig.json           # Configuration TypeScript CIF
- src/lib/utils.ts        # Helpers CIF

# Composants UI à ajouter dans src/components/ui/ :
- Button.tsx
- Card.tsx
- Dialog.tsx
- DropdownMenu.tsx
- Input.tsx
- Label.tsx
- Modal.tsx
- ProgressBar.tsx
- Select.tsx
- Toaster.tsx
- Tooltip.tsx
```

### 4. Lancer le serveur de développement

```bash
npm run dev
```

L'application sera accessible sur `http://localhost:3000`

## 🔐 Authentification

L'authentification est gérée via **Supabase Auth** :

1. Login avec email/password
2. Token JWT automatiquement ajouté aux requêtes API
3. Routes protégées avec `<ProtectedRoute>`
4. Auth state global via `AuthContext`

### Créer un compte de test

Dans le dashboard Supabase :
1. Authentication → Users → Add User
2. Email: `test@example.com`
3. Password: créer un mot de passe
4. User Metadata: `{ "role": "courtier" }`

### Compte Admin

Pour accéder aux endpoints admin :
1. Créer un utilisateur Supabase
2. Définir `role: "admin"` dans les User Metadata
3. OU ajouter l'email dans `ADMIN_EMAIL` du backend

## 📦 Scripts

```bash
npm run dev         # Lancer dev server (port 3000)
npm run build       # Build production
npm run preview     # Prévisualiser build
```

## 🛠️ Développement

### Ajouter une nouvelle page

1. Créer le composant dans `src/pages/`
2. Ajouter la route dans `src/App.tsx`
3. Ajouter le lien de navigation dans `src/components/layout/Sidebar.tsx`

### Appeler l'API backend

Utiliser les services dans `src/services/` :

```typescript
import { listDossiers } from '../services/dossiers';

// Dans un composant
const [dossiers, setDossiers] = useState([]);

useEffect(() => {
  listDossiers().then(setDossiers);
}, []);
```

Le JWT est automatiquement ajouté par l'intercepteur Axios.

### Utiliser l'auth context

```typescript
import { useAuth } from '../contexts/AuthContext';

function MyComponent() {
  const { user, isAdmin, logout } = useAuth();

  return (
    <div>
      <p>Connecté : {user?.email}</p>
      {isAdmin && <p>Admin</p>}
      <button onClick={logout}>Déconnexion</button>
    </div>
  );
}
```

## 🎨 Design System Capital In Fine

### Classes CSS disponibles

```css
/* Colors */
.text-cif-primary
.bg-cif-primary
.border-cif-primary

/* Content */
.text-content-primary    /* Texte principal */
.text-content-secondary  /* Texte secondaire */
.text-content-tertiary   /* Texte tertiaire */

/* Surfaces */
.bg-surface-bg          /* Background global */
.bg-surface-default     /* Cards, panels */
.bg-surface-hover       /* Hover state */

/* Edges */
.border-edge-default

/* Alerts */
.alert-cif-error
.alert-cif-success
.alert-cif-warning
.alert-cif-info

/* Sidebar */
.sidebar-cif
.sidebar-cif-item
.sidebar-cif-item-active
```

### Composants UI

Tous les composants sont dans `src/components/ui/` et suivent le design Capital In Fine.

## 📝 Session 8 - État actuel

✅ **Terminé** :
- Setup projet Vite + React + TypeScript
- Auth Supabase (login, signup, logout, protected routes)
- Layout (Header, Sidebar, Layout principal)
- Routing (dashboard, dossiers, admin)
- API client (axios + JWT interceptors)
- Services (auth, dossiers, admin)
- Types TypeScript complets

⏳ **À compléter** :
- Intégrer les composants UI Capital In Fine fournis
- Compléter `.env.local` avec credentials Supabase

## 📋 Sessions suivantes

**Session 9** : Dashboard complet
- Statistiques (nb dossiers, progression)
- Liste dossiers avec filtres et recherche
- Graphiques de suivi

**Session 10** : Page Détail Dossier
- Informations client complètes
- Liste des pièces avec statuts
- Upload documents
- Timeline activités

**Session 11** : Administration
- CRUD courtiers
- Statistiques globales
- Gestion des accès

## 🔗 API Backend

L'API backend doit tourner sur `http://localhost:8000`.

Endpoints utilisés :
- `GET /api/dossiers` - Liste dossiers
- `GET /api/dossiers/:id` - Détail dossier
- `PATCH /api/dossiers/:id` - Mise à jour
- `POST /api/dossiers/:id/validate` - Marquer complet
- `GET /api/admin/courtiers` - Liste courtiers (admin)
- `POST /api/admin/courtiers` - Créer courtier (admin)

## 📞 Support

Pour toute question, consulter la documentation du projet principal Léonie.
