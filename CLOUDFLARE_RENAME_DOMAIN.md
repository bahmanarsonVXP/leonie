# 🌐 Changer le domaine Cloudflare Pages

## Situation actuelle

Votre projet est actuellement déployé sur :
- **Domaine actuel** : `leonie-cz6.pages.dev`
- **Nom du projet** : `leonie`

## ⚠️ Limitation importante

**Vous ne pouvez PAS renommer directement un projet Cloudflare Pages** pour changer le domaine `.pages.dev`. Le domaine est généré automatiquement et dépend du nom du projet.

## ✅ Solutions possibles

### Option 1 : Supprimer et recréer le projet (RECOMMANDÉ)

Si vous voulez absolument `leonie.pages.dev` ou `leonie-voxperience.pages.dev`, vous devez :

1. **Noter les configurations actuelles** :
   - Variables d'environnement
   - Configuration de build (root directory, build command)
   - Connexion Git

2. **Supprimer le projet actuel** :
   ```bash
   npx wrangler pages project delete leonie
   ```
   ⚠️ **ATTENTION** : Cela supprimera tous les déploiements existants !

3. **Créer un nouveau projet avec le nom souhaité** :
   ```bash
   npx wrangler pages project create leonie-voxperience --production-branch=main
   ```

4. **Reconnecter le repo GitHub** :
   - Via le Dashboard Cloudflare
   - Workers & Pages → leonie-voxperience → Settings → Source → Connect Git

5. **Reconfigurer** :
   - Variables d'environnement
   - Build settings (root directory: `frontend`)

### Option 2 : Utiliser un domaine personnalisé (MEILLEURE SOLUTION)

Au lieu de changer le domaine `.pages.dev`, ajoutez un domaine personnalisé :

1. **Dans Cloudflare Dashboard** :
   - Workers & Pages → leonie → **Custom domains**
   - Cliquez sur **Set up a custom domain**

2. **Ajouter un domaine** :
   - Si vous avez un domaine (ex: `voxperience.com`), ajoutez :
     - `leonie.voxperience.com` ou
     - `leonie-voxperience.voxperience.com`
   - Cloudflare configurera automatiquement les DNS

3. **Avantages** :
   - ✅ Garde votre projet actuel
   - ✅ Pas besoin de reconfigurer
   - ✅ Domaine professionnel (meilleur que .pages.dev)
   - ✅ Le domaine `.pages.dev` reste actif aussi

### Option 3 : Garder le domaine actuel

Le domaine `leonie-cz6.pages.dev` fonctionne parfaitement. Vous pouvez :
- L'utiliser tel quel
- Ajouter un domaine personnalisé en plus (Option 2)

## 📋 Commandes CLI utiles

### Voir les projets existants
```bash
npx wrangler pages project list
```

### Voir si un nom est disponible
Les noms de projets doivent être uniques dans votre compte. Pour vérifier :
```bash
npx wrangler pages project list | grep "nom-du-projet"
```

### Supprimer un projet
```bash
npx wrangler pages project delete leonie
```

### Créer un nouveau projet
```bash
npx wrangler pages project create leonie-voxperience --production-branch=main
```

## 🎯 Recommandation

**Option 2 (Domaine personnalisé)** est la meilleure car :
- ✅ Pas de perte de données
- ✅ Pas besoin de reconfigurer
- ✅ Domaine professionnel
- ✅ Plus flexible pour l'avenir

Si vous voulez vraiment changer le nom du projet, l'**Option 1** est possible mais nécessite une reconfiguration complète.

## ⚠️ Note importante

J'ai vu dans votre liste de projets qu'il existe déjà :
- `leonie` → `leonie-cz6.pages.dev` (votre projet actuel)
- `leonieback` → `leonie.pages.dev` (probablement un autre projet)

Le domaine `leonie.pages.dev` est donc **déjà utilisé** par un autre projet (`leonieback`). Vous ne pouvez pas utiliser ce nom sauf si vous supprimez `leonieback` d'abord.

