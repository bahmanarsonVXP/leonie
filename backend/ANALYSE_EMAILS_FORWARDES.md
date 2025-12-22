# Analyse: Emails forwardés par le courtier

## 📋 Scénario

1. **Courtier discute au téléphone** avec un client
2. **Courtier donne la liste** des pièces à fournir
3. **Client envoie les pièces** directement au courtier (jean.dupont@gmail.com → beamkx@gmail.com)
4. **Courtier forward à Léonie** (beamkx@gmail.com → leonie@voxperience.com)

## 🔍 Comportement actuel (Session 6)

### ✅ Ce qui fonctionne bien

1. **Identification courtier**: ✅ PARFAIT
   - L'expéditeur (beamkx@gmail.com) est correctement identifié comme le courtier

2. **Classification Mistral**: ✅ EXCELLENT
   - Action détectée: `ENVOI_DOCUMENTS` (98% confiance)
   - Mistral extrait correctement du **contenu** de l'email:
     - `client_nom: "Dupont"`
     - `client_prenom: "Jean"`
     - `nombre_pieces: 2`
   - Le résumé est pertinent: "Client envoie des documents réels (CNI et justificatif de domicile)"

3. **Upload pièces jointes**: ✅ FONCTIONNE
   - Les pièces sont uploadées sur Google Drive
   - Le fichier est sauvegardé sans erreur

### ⚠️ Ce qui pose problème

1. **Identification client**: ❌ ÉCHOUE
   ```
   Recherche par from_address: beamkx@gmail.com → C'est le courtier!
   Recherche par TO/CC: leonie@voxperience.com → Adresse système
   Résultat: Aucun client trouvé
   ```
   **Pourquoi?** L'email original du client (`jean.dupont@gmail.com`) est dans le **corps** de l'email, pas dans les headers.

2. **Destination upload**: ❌ MAUVAIS DOSSIER
   ```python
   # Dans process_envoi_documents() ligne 275
   client_folder_id = drive.master_folder_id  # Placeholder Session 6
   ```
   **Résultat**: Les pièces sont uploadées dans le **dossier principal** au lieu du dossier client.

3. **Pas de DB update**: ❌ NON IMPLÉMENTÉ
   - Les pièces ne sont pas enregistrées en base de données
   - Pas de lien avec un dossier client
   - Le courtier ne peut pas suivre l'état des documents

## 💡 Solutions (à implémenter en Session 7+)

### Solution 1: Parser les headers de forward (RECOMMANDÉ)

Détecter automatiquement les emails forwardés en analysant les headers IMAP:

```python
def detect_forwarded_email(email: EmailData) -> Optional[Dict]:
    """
    Détecte si l'email est un forward et extrait les informations originales.

    Returns:
        Dict avec 'original_from', 'original_to', 'original_subject' ou None
    """
    # 1. Vérifier le sujet
    if not email.subject.startswith(('Fwd:', 'Fw:', 'TR:')):
        return None

    # 2. Parser le corps pour extraire les headers originaux
    patterns = [
        r'From:.*?<(.+?)>',
        r'De:.*?<(.+?)>',
        # Autres patterns...
    ]

    # 3. Retourner les infos extraites
    return {
        'original_from': 'jean.dupont@gmail.com',
        'original_subject': 'Documents pour mon dossier',
        'is_forwarded': True
    }
```

### Solution 2: Utiliser Mistral pour identifier le client

Mistral extrait déjà le nom du client (`Jean Dupont`) - utilisons-le!

```python
# Dans process_envoi_documents()
details = classification.get('details', {})
client_nom = details.get('client_nom')
client_prenom = details.get('client_prenom')

if client_nom:
    # Chercher le client par nom (et courtier_id)
    client = db.find_client_by_name(courtier_id, client_nom, client_prenom)

    if client:
        logger.info(f"Client identifié par nom: {client_prenom} {client_nom}")
        client_folder_id = client.get('dossier_drive_id')
    else:
        logger.warning(f"Client '{client_prenom} {client_nom}' non trouvé en base")
        # Envoyer notification au courtier pour confirmation
```

### Solution 3: Notification courtier (ESSENTIEL)

Quand un client n'est pas trouvé, demander au courtier:

```python
# Via NotificationService (Session 7)
await notif.send_email(
    to=courtier.email,
    subject="⚠️ Client non identifié - Documents reçus",
    body=f"""
    Bonjour {courtier.prenom},

    J'ai reçu un email avec des documents, mais je n'ai pas pu identifier
    automatiquement le client concerné.

    Informations détectées:
    - Client probable: {client_prenom} {client_nom}
    - Documents: {nombre_pieces} pièce(s) jointe(s)
    - Fichiers: {', '.join(filenames)}

    Les documents sont temporairement dans le dossier principal.

    Merci de:
    1. Vérifier si le client existe déjà dans votre liste
    2. Créer le client s'il est nouveau
    3. Je déplacerai automatiquement les documents dans le bon dossier

    Léonie 🤖
    """
)
```

### Solution 4: Interface de confirmation (IDÉAL - Session 8+)

Créer une interface web où le courtier peut:
- Voir les documents en attente
- Les associer à un client existant (dropdown)
- Créer un nouveau client si nécessaire
- Valider le classement

## 📊 Recommandation d'implémentation

### Session 7 (Court terme):

1. ✅ **Implémenter Solution 2**: Recherche client par nom via Mistral
   - Rapide à implémenter
   - Fonctionne dans 80% des cas
   - Pas de dépendance externe

2. ✅ **Implémenter Solution 3**: Notifications courtier
   - Critique pour la production
   - Permet au courtier de corriger les erreurs
   - Évite la perte de documents

3. 🔄 **Améliorer process_envoi_documents()**:
   ```python
   # Ordre de recherche client:
   # 1. Par email (si disponible)
   # 2. Par nom extrait par Mistral
   # 3. Fallback: dossier temporaire + notification courtier
   ```

### Session 8+ (Moyen terme):

4. 🚀 **Parser headers de forward** (Solution 1)
   - Plus robuste
   - Meilleure UX
   - Nécessite plus de développement

5. 🚀 **Interface de confirmation** (Solution 4)
   - UX optimale
   - Courtier garde le contrôle
   - Nécessite frontend

## 🧪 Test de validation

Script de test créé: `test_scenario_forward.py`

Résultat actuel:
- ✅ Classification: ENVOI_DOCUMENTS (98%)
- ✅ Upload: Fichier uploadé sur Drive
- ⚠️ Dossier: Master folder (pas le dossier client)
- ❌ Client: Non identifié

Résultat attendu après Session 7:
- ✅ Classification: ENVOI_DOCUMENTS
- ✅ Upload: Fichier uploadé
- ✅ Dossier: Dossier client Jean Dupont
- ✅ Client: Identifié par nom via Mistral
- ✅ Notification: Email envoyé au courtier si ambiguïté

## 📝 Notes techniques

### Headers email forward Gmail

Quand Gmail forward un email, les headers incluent:
```
X-Forwarded-To: leonie@voxperience.com
X-Forwarded-For: jean.dupont@gmail.com
References: <original-message-id>
In-Reply-To: <original-message-id>
```

Ces headers peuvent être exploités pour identifier l'expéditeur original.

### Formats de forward détectables

- Gmail: `---------- Forwarded message ---------`
- Outlook: `-----Original Message-----`
- Apple Mail: `Begin forwarded message:`
- Format universel: Sujet commence par `Fwd:`, `Fw:`, `TR:`

### Patterns regex pour extraction

```python
import re

# Extraire l'email original
email_pattern = r'(?:From|De|Fra):\s*(?:.*?)<(.+?)>|(?:From|De|Fra):\s*(\S+@\S+)'

# Extraire le nom
name_pattern = r'(?:From|De|Fra):\s*([^<]+?)\s*<'
```
