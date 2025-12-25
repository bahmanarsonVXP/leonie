# ⚠️ Variables d'environnement manquantes dans Railway

## Problème

Le déploiement Railway échoue avec l'erreur :
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
ADMIN_EMAIL
  Field required [type=missing]
```

## Solution

Ajouter la variable `ADMIN_EMAIL` dans Railway.

### Via Railway Dashboard

1. Allez sur https://railway.app
2. Sélectionnez votre projet → Service `web`
3. Onglet **Variables**
4. Cliquez sur **+ New Variable**
5. Ajoutez :
   - **Name** : `ADMIN_EMAIL`
   - **Value** : `admin@voxperience.com` (ou votre email admin)

### Via CLI

```bash
railway variables set ADMIN_EMAIL=admin@voxperience.com
```

## Variables requises depuis Session 7

Si vous avez implémenté la Session 7 (API REST + Auth), vérifiez aussi que ces variables sont présentes :

- ✅ `ADMIN_EMAIL` - **MANQUANTE** (cause de l'erreur actuelle)
- ⚠️ `SUPABASE_JWT_SECRET` - Vérifier si présente (requis pour auth JWT)

### Vérifier toutes les variables

```bash
railway variables
```

## Après ajout

Une fois `ADMIN_EMAIL` ajoutée, Railway va automatiquement redéployer.

Ou forcer un redéploiement :
```bash
railway up
```

