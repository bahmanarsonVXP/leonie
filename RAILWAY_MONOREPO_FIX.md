# 🔧 Fix déploiement Railway - Structure Monorepo

## Problème

Après la réorganisation en monorepo (`backend/` + `frontend/`), Railway ne trouvait plus les fichiers car il cherchait à la racine.

## Solution appliquée

### 1. Création d'un Dockerfile à la racine

Un nouveau `Dockerfile` a été créé à la racine du monorepo qui :
- Copie les fichiers depuis `backend/` explicitement
- Utilise le même script `start.sh` pour démarrer l'application
- Fonctionne avec Railway depuis la racine du repo

### 2. Configuration railway.json

Le fichier `railway.json` à la racine indique :
- `dockerfilePath: "Dockerfile"` (à la racine)
- Même configuration de déploiement (healthcheck, restart policy, etc.)

## Structure des fichiers

```
leonie/
├── Dockerfile          ← NOUVEAU : Dockerfile adapté pour monorepo
├── railway.json        ← NOUVEAU : Configuration Railway à la racine
├── backend/
│   ├── Dockerfile      ← Ancien (peut être supprimé)
│   ├── railway.json    ← Ancien (peut être supprimé)
│   ├── main.py
│   ├── requirements.txt
│   └── start.sh        ← Utilisé par le Dockerfile racine
└── frontend/
    └── ...
```

## Déploiement

Railway va maintenant :
1. Détecter le `Dockerfile` à la racine
2. Build depuis le contexte racine
3. Copier uniquement les fichiers depuis `backend/`
4. Lancer l'application avec `/app/start.sh`

## Prochaines étapes

1. **Commiter les changements** :
   ```bash
   git add Dockerfile railway.json
   git commit -m "fix: Adapter Dockerfile pour structure monorepo Railway"
   git push
   ```

2. **Railway va redéployer automatiquement** (si GitHub est connecté)

3. **Vérifier les logs** :
   ```bash
   railway logs --tail 100
   ```

## Notes

- L'ancien `backend/Dockerfile` et `backend/railway.json` peuvent être supprimés
- Le `Dockerfile` racine copie explicitement depuis `backend/` pour éviter de copier `frontend/`
- Le script `start.sh` reste dans `backend/` et est copié dans l'image

