# 🔧 Fix : Variables d'environnement non disponibles au build Cloudflare Pages

## Problème

Les logs Cloudflare montrent :
```
Build environment variables: (none found)
```

Même si les variables sont configurées dans Cloudflare Dashboard, elles ne sont pas disponibles pendant le build Vite.

## Cause

Dans Cloudflare Pages, les variables d'environnement peuvent être configurées pour :
1. **Build time** (pendant `npm run build`) - REQUIS pour Vite
2. **Runtime** (dans le navigateur) - Pas nécessaire pour Vite car les variables sont injectées au build

## ✅ Solution : Vérifier la configuration dans Cloudflare Dashboard

### Étape 1 : Vérifier que les variables sont dans la bonne section

1. Allez sur https://dash.cloudflare.com/
2. Workers & Pages → Votre projet `leonie`
3. **Settings** → **Environment variables**
4. **IMPORTANT** : Vérifiez que vous êtes dans l'onglet **Production** (pas Preview)
5. Vérifiez que les variables sont bien listées :
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_API_URL`

### Étape 2 : S'assurer que les variables sont disponibles au BUILD

Dans Cloudflare Pages, les variables d'environnement sont **par défaut** disponibles au build ET au runtime. Mais vérifiez :

1. Dans **Environment variables**, pour chaque variable :
   - Elles doivent être dans la section **Production** (pas Preview seulement)
   - Pas besoin de case à cocher spéciale - elles sont automatiquement disponibles au build

### Étape 3 : Vérifier le Root directory

Assurez-vous que le **Root directory** est bien configuré à `frontend` :
- Settings → **Builds & deployments**
- **Root directory (Path)** = `frontend`

### Étape 4 : Alternative - Créer un fichier .env.production

Si les variables ne sont toujours pas disponibles, vous pouvez créer un fichier `.env.production` dans `frontend/` (mais attention : ne pas commiter les secrets !).

Cependant, la meilleure solution est de configurer correctement dans Cloudflare Dashboard.

## Vérification

Pour vérifier que les variables sont disponibles, vous pouvez temporairement ajouter dans `vite.config.ts` :

```typescript
export default defineConfig({
  // ...
  define: {
    'process.env': process.env, // Pour debug
  },
})
```

Et dans le code, ajouter un log :
```typescript
console.log('VITE_SUPABASE_URL:', import.meta.env.VITE_SUPABASE_URL);
```

Mais le plus simple est de vérifier dans Cloudflare Dashboard que les variables sont bien configurées pour Production.

## Solution de contournement temporaire

Si vraiment les variables ne passent pas au build, vous pouvez créer un fichier `frontend/.env.production` avec :
```
VITE_SUPABASE_URL=https://wybypzuuyxzgdtmslcko.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
VITE_API_URL=https://web-production-b71d4.up.railway.app/api
```

**⚠️ ATTENTION** : Ce fichier sera committé dans Git si vous ne l'ignorez pas. Pour les secrets, préférez Cloudflare Dashboard.

Mais pour `.env.production`, c'est acceptable car Vite l'utilise seulement en mode production.

