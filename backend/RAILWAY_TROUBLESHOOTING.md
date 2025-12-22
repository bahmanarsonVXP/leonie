# Dépannage Railway - Healthcheck Failed

## 🔴 Problème : Healthcheck Failed

Si vous voyez l'erreur `Healthcheck failed!` ou `1/1 replicas never became healthy!`, voici les causes possibles :

## ✅ Solutions

### 1. Vérifier les variables d'environnement obligatoires

L'application **DOIT** avoir ces variables définies pour démarrer :

```bash
# OBLIGATOIRES (sans elles, l'app ne démarre pas)
SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_KEY=votre-clé-api-supabase
IMAP_EMAIL=leonie.capitalinfinie@gmail.com
IMAP_PASSWORD=votre-app-password
MISTRAL_API_KEY=votre-clé-mistral
API_SECRET_KEY=votre-clé-secrète

# RECOMMANDÉES
ENVIRONMENT=production
IMAP_HOST=imap.gmail.com
IMAP_LABEL=INBOX
```

**Action** : Vérifier dans Railway → Variables que toutes ces variables sont définies.

### 2. PORT est automatique (ne pas l'ajouter)

⚠️ **IMPORTANT** : La variable `PORT` est **automatiquement définie par Railway**. 
- ❌ Ne pas l'ajouter dans les variables d'environnement
- ✅ Railway l'injecte automatiquement
- ✅ Le Dockerfile/Procfile l'utilise automatiquement

### 3. Vérifier les logs de démarrage

Dans Railway → Logs, chercher les erreurs au démarrage :

**Erreurs courantes** :
- `SUPABASE_URL must be defined` → Variable manquante
- `Error connecting to...` → Problème de connexion
- `ModuleNotFoundError` → Dépendance manquante
- `Port already in use` → Conflit de port (rare)

### 4. Vérifier que le service démarre correctement

Le service doit afficher dans les logs :
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:XXXX
```

### 5. Augmenter le timeout du healthcheck

Si l'application met du temps à démarrer, augmenter le timeout dans `railway.json` :

```json
{
  "deploy": {
    "healthcheckTimeout": 200  // Augmenter à 200 secondes
  }
}
```

### 6. Vérifier le Dockerfile

Le Dockerfile doit utiliser `${PORT}` :

```dockerfile
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## 🔍 Diagnostic étape par étape

1. **Vérifier les variables** : Railway → Variables → Toutes les variables obligatoires sont-elles là ?
2. **Vérifier les logs** : Railway → Logs → Y a-t-il des erreurs au démarrage ?
3. **Vérifier le build** : Railway → Deployments → Le build a-t-il réussi ?
4. **Tester localement** : L'application démarre-t-elle avec les mêmes variables ?

## 📝 Checklist de déploiement

- [ ] Toutes les variables obligatoires sont définies dans Railway
- [ ] `PORT` n'est PAS dans les variables (Railway le définit automatiquement)
- [ ] Le build Docker réussit sans erreur
- [ ] Les logs montrent "Application startup complete"
- [ ] Le healthcheck atteint `/health` avec succès

## 🆘 Si rien ne fonctionne

1. Vérifier que l'application démarre localement avec les mêmes variables
2. Vérifier les logs complets dans Railway
3. Tester l'endpoint `/health` manuellement si possible
4. Vérifier que le port exposé correspond à celui utilisé par Railway

