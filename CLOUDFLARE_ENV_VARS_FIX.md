# 🔧 Fix : Variables d'environnement Supabase manquantes sur Cloudflare Pages

## Problème

Erreur en production :
```
Uncaught Error: Missing Supabase environment variables. Check .env.local file.
```

## Cause

Les variables d'environnement `VITE_SUPABASE_URL` et `VITE_SUPABASE_ANON_KEY` ne sont pas configurées dans Cloudflare Pages ou ne sont pas accessibles au moment du build.

## ✅ Solution : Configurer les variables dans Cloudflare Pages

### Via Dashboard Cloudflare

1. **Allez sur** : https://dash.cloudflare.com/
2. **Naviguez vers** : Workers & Pages → Votre projet (ex: `leonie`)
3. **Cliquez sur** : Settings → **Environment variables**
4. **Vérifiez que ces 2 variables sont présentes** :

#### Variable 1 : VITE_SUPABASE_URL
```
Name: VITE_SUPABASE_URL
Value: https://wybypzuuyxzgdtmslcko.supabase.co
```

#### Variable 2 : VITE_SUPABASE_ANON_KEY
```
Name: VITE_SUPABASE_ANON_KEY
Value: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind5YnlwenV1eXh6Z2R0bXNsY2tvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU3NzQxNjQsImV4cCI6MjA4MTM1MDE2NH0.duIB8Eqe--DH-6V5W-77B8u00NcByqm6_vLJ7MtDs08
```

#### Variable 3 : VITE_API_URL (optionnel mais recommandé)
```
Name: VITE_API_URL
Value: https://web-production-b71d4.up.railway.app/api
```

### Important ⚠️

1. **Redéployez après modification** :
   - Allez dans **Deployments**
   - Cliquez sur les **3 points** (⋯) du dernier déploiement
   - Sélectionnez **Retry deployment**

2. **Les variables doivent être dans la section "Production"** :
   - Vérifiez que vous configurez les variables pour **Production**
   - Si vous avez des environnements Preview, configurez-les aussi si nécessaire

3. **Format des variables** :
   - Les variables Vite doivent commencer par `VITE_` pour être accessibles dans le code frontend
   - Pas d'espaces avant/après les valeurs
   - Pas de guillemets autour des valeurs

## Vérification

Après redéploiement, l'erreur devrait disparaître et l'application devrait se charger correctement.

## Test

Ouvrez la console du navigateur sur votre site Cloudflare et vérifiez qu'il n'y a plus l'erreur "Missing Supabase environment variables".

