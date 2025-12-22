# Guide de test - Validation dossier_drive_id

## Tests à effectuer

### Test 1 : Vérifier que le code utilise directement le dossier_drive_id

**Commande :**
```bash
python test_dossier_drive_validation.py
```

**Résultat attendu :**
- Si le courtier a un `dossier_drive_id` valide → le dossier client est créé ✅
- Si le courtier a un `dossier_drive_id` invalide → `RuntimeError` est levée ✅

### Test 2 : Test avec un email réel

**Étapes :**
1. Assurez-vous que le courtier BEAMKX a un `dossier_drive_id` **valide** dans Supabase
2. Envoyez un email à Leonie avec le sujet "Créer un dossier pour [Nom] [Prénom]"
3. Vérifiez les logs du worker RQ

**Commande pour déclencher le traitement :**
```bash
python test_nouvel_email_beamkx.py
```

**Résultat attendu :**
- Le dossier client est créé dans le dossier courtier sur Google Drive
- Aucune erreur dans les logs

### Test 3 : Test avec un courtier ayant un dossier invalide

**Étapes :**
1. Dans Supabase, modifiez temporairement le `dossier_drive_id` d'un courtier avec un ID invalide (ex: `fake-id-123`)
2. Exécutez le test :
```bash
python test_job_direct.py
```

**Résultat attendu :**
- Une `RuntimeError` est levée avec un message clair indiquant que le dossier est invalide

### Test 4 : Vérification manuelle sur Google Drive

**Étapes :**
1. Allez sur Google Drive
2. Ouvrez le dossier maître (ID dans `GOOGLE_DRIVE_MASTER_FOLDER_ID`)
3. Vérifiez que le dossier courtier existe
4. Vérifiez que le dossier client a été créé à l'intérieur

**Commande pour lister les dossiers :**
```bash
python check_dossier_created.py
```

## Scénarios de test

### ✅ Scénario 1 : Courtier valide → Succès
- Courtier avec `dossier_drive_id` valide
- Résultat : Dossier client créé avec succès

### ❌ Scénario 2 : Courtier sans dossier_drive_id → ValueError
- Courtier avec `dossier_drive_id = NULL`
- Résultat : `ValueError` avec message explicite

### ❌ Scénario 3 : Courtier avec dossier invalide → RuntimeError
- Courtier avec `dossier_drive_id` qui n'existe pas sur Drive
- Résultat : `RuntimeError` avec message explicite

## Commandes utiles

### Vérifier le dossier_drive_id d'un courtier
```bash
python -c "from app.utils.db import get_courtier_by_email; c = get_courtier_by_email('beamkx@gmail.com'); print(f\"dossier_drive_id: {c.get('dossier_drive_id')}\")"
```

### Vérifier si un dossier existe sur Drive
```bash
python -c "from app.services.drive import DriveManager; d = DriveManager(); d.service.files().get(fileId='VOTRE_ID', fields='id,name', supportsAllDrives=True).execute(); print('✅ Dossier existe')"
```

### Lister les dossiers créés
```bash
python check_dossier_created.py
```

