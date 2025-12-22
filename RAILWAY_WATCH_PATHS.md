# 🎯 Configuration Watch Paths Railway pour Monorepo

## ✅ Oui, configurez Watch Paths à `/backend/**`

Pour éviter que Railway redéploie inutilement quand vous modifiez le `frontend/`, configurez les **Watch Paths**.

## 📋 Configuration recommandée

Dans **Railway Dashboard** → Votre projet → Service `web` → **Settings** → **Watch Paths** :

Ajoutez ces chemins (un par ligne ou séparés par des virgules) :

```
backend/**
Dockerfile
railway.json
```

## 🔍 Explication

- **`backend/**`** : Surveille tous les fichiers dans le dossier backend
- **`Dockerfile`** : Surveille le Dockerfile à la racine (utilisé pour le build)
- **`railway.json`** : Surveille la config Railway (peut déclencher un redéploiement)

## ✅ Résultat

Railway ne redéploiera QUE quand :
- ✅ Un fichier dans `backend/` change
- ✅ Le `Dockerfile` change
- ✅ Le `railway.json` change

Railway NE redéploiera PAS quand :
- ❌ Un fichier dans `frontend/` change (normal, c'est déployé sur Cloudflare)
- ❌ Un fichier de documentation change
- ❌ D'autres fichiers à la racine changent (README, etc.)

## ⚠️ Note importante

Si vous utilisez le **nouveau builder v2** de Railway et que les Watch Paths semblent ignorés :
1. Vérifiez dans Settings → Builder
2. Si nécessaire, revenez à l'ancien builder

## 📸 Où trouver dans Railway Dashboard

1. Ouvrez votre projet Railway
2. Cliquez sur le service `web`
3. Onglet **Settings**
4. Section **Source** ou **Watch Paths**
5. Ajoutez les chemins ci-dessus
6. Sauvegardez

---

**Configuration optimale pour un monorepo !** 🚀

