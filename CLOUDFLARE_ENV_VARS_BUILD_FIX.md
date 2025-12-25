# 🔧 Fix : Variables Vite non injectées au build

## Problème

Les variables d'environnement sont configurées dans Cloudflare Pages, mais l'erreur persiste :
```
Missing Supabase environment variables
```

## Cause

**Vite injecte les variables `import.meta.env.VITE_*` au moment du BUILD**, pas au runtime. Si les variables n'étaient pas présentes lors du dernier build, elles seront `undefined` dans le code compilé.

## ✅ Solution : Forcer un nouveau build

### Option 1 : Redéploiement avec rebuild (RECOMMANDÉ)

1. **Dans Cloudflare Dashboard** :
   - Workers & Pages → Votre projet
   - **Deployments**
   - Cliquez sur les **3 points** (⋯) du dernier déploiement
   - **Retry deployment** OU **Rebuild deployment**

2. **Cela va** :
   - Relancer le build (`npm run build`)
   - Injecter les variables d'environnement dans le code
   - Redéployer avec les variables correctes

### Option 2 : Push un changement pour déclencher un nouveau build

Faites un petit changement dans le code frontend pour forcer un nouveau build :

```bash
# Faites un petit changement (commentaire, etc.)
# Puis commit et push
git add .
git commit -m "chore: Force rebuild avec variables env"
git push
```

### Option 3 : Vérifier que les variables sont dans "Production"

1. Cloudflare Dashboard → Votre projet → **Settings**
2. **Environment variables**
3. Vérifiez que vous êtes dans l'onglet **Production** (pas Preview)
4. Les variables doivent être visibles dans la section **Production**

### Option 4 : Utiliser wrangler.toml pour les variables (alternative)

Si le problème persiste, vous pouvez aussi définir les variables dans `wrangler.toml` :

```toml
[vars]
VITE_SUPABASE_URL = "https://wybypzuuyxzgdtmslcko.supabase.co"
VITE_SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
VITE_API_URL = "https://web-production-b71d4.up.railway.app/api"
```

Mais normalement, les variables dans le Dashboard devraient suffire.

## Vérification

Après le redéploiement, vérifiez dans les logs de build Cloudflare que :
- Les variables sont bien chargées
- Le build se termine avec succès
- Pas d'erreur "undefined" ou "missing"

## Note importante

**Avec Vite, les variables d'environnement sont remplacées au BUILD**, donc :
- ✅ Si vous ajoutez/modifiez des variables → **Redéployez** (nouveau build requis)
- ❌ Les variables ne sont PAS injectées au runtime comme avec d'autres frameworks

