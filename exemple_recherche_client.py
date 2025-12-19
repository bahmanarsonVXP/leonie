#!/usr/bin/env python3
"""
Exemple concret de recherche de client dans la base de données.

Ce script montre étape par étape comment le système vérifie
si un client existe dans Supabase.
"""

# ============================================================================
# ÉTAPE 1 : Email reçu et parsé (déjà fait par EmailFetcher via IMAP)
# ============================================================================

email_reçu = {
    "from_address": "sophie.martin@email.com",  # Expéditeur
    "to_addresses": ["leonie@voxperience.com"],  # Destinataire
    "cc_addresses": ["jean.martin@email.com"],   # En copie (co-emprunteur)
    "subject": "Documents pour mon dossier",
    "body": "Bonjour, voici mes documents..."
}

print("=" * 80)
print("ÉTAPE 1 : Email reçu (déjà parsé depuis IMAP)")
print("=" * 80)
print(f"De: {email_reçu['from_address']}")
print(f"À: {email_reçu['to_addresses']}")
print(f"CC: {email_reçu['cc_addresses']}")
print()

# ============================================================================
# ÉTAPE 2 : Courtier identifié (déjà fait)
# ============================================================================

courtier_id = "123e4567-e89b-12d3-a456-426614174000"
print("=" * 80)
print("ÉTAPE 2 : Courtier identifié")
print("=" * 80)
print(f"Courtier ID: {courtier_id}")
print()

# ============================================================================
# ÉTAPE 3 : Recherche du client - Étape 1 : Par email expéditeur
# ============================================================================

print("=" * 80)
print("ÉTAPE 3 : Recherche du client dans Supabase")
print("=" * 80)
print()

sender_email = email_reçu["from_address"]
print(f"3.1 Recherche par email expéditeur: {sender_email}")
print(f"   → Requête Supabase:")
print(f"   SELECT * FROM clients")
print(f"   WHERE email_principal = '{sender_email}'")
print(f"   AND courtier_id = '{courtier_id}'")
print()

# Simuler le résultat
client_trouvé_par_expéditeur = None  # None = pas trouvé
print(f"   → Résultat: {client_trouvé_par_expéditeur}")
print(f"   → Client non trouvé par email expéditeur")
print()

# ============================================================================
# ÉTAPE 4 : Recherche dans tous les emails (TO, CC)
# ============================================================================

print("=" * 80)
print("ÉTAPE 4 : Recherche étendue dans tous les emails")
print("=" * 80)
print()

# Construire la liste de tous les emails
all_emails = [sender_email] + email_reçu["to_addresses"] + email_reçu["cc_addresses"]
print(f"4.1 Liste de tous les emails de l'email:")
print(f"   {all_emails}")
print()

# Filtrer les adresses système
system_emails = [
    "leonie@voxperience.com",
    "contact@voxperience.com",
    "noreply@voxperience.com"
]
all_emails_filtrés = [
    e for e in all_emails
    if e.lower() not in [s.lower() for s in system_emails]
]
print(f"4.2 Après filtrage des adresses système:")
print(f"   {all_emails_filtrés}")
print(f"   (leonie@voxperience.com a été retiré)")
print()

# ============================================================================
# ÉTAPE 5 : Recherche dans Supabase pour chaque email
# ============================================================================

print("=" * 80)
print("ÉTAPE 5 : Recherche dans Supabase pour chaque email")
print("=" * 80)
print()

# Simuler la base de données Supabase
clients_en_base = [
    {
        "id": "client-1",
        "courtier_id": courtier_id,
        "nom": "Martin",
        "prenom": "Sophie",
        "email_principal": "sophie.martin@email.com",  # ✅ Trouvé !
        "emails_secondaires": ["jean.martin@email.com"]  # Co-emprunteur
    },
    {
        "id": "client-2",
        "courtier_id": courtier_id,
        "nom": "Dupont",
        "prenom": "Jean",
        "email_principal": "jean.dupont@email.com",
        "emails_secondaires": []
    }
]

print("5.1 Recherche par email principal:")
for email in all_emails_filtrés:
    print(f"   → Recherche: {email}")
    # Simuler la requête Supabase
    for client in clients_en_base:
        if client["email_principal"] == email and client["courtier_id"] == courtier_id:
            print(f"     ✅ TROUVÉ ! Client: {client['prenom']} {client['nom']}")
            print(f"     → ID: {client['id']}")
            client_trouvé = client
            break
    else:
        print(f"     ❌ Non trouvé")
    print()

# Si pas trouvé par email principal, chercher dans emails secondaires
if 'client_trouvé' not in locals():
    print("5.2 Recherche par emails secondaires:")
    print(f"   → Récupération de tous les clients du courtier depuis Supabase")
    print(f"   SELECT * FROM clients WHERE courtier_id = '{courtier_id}'")
    print()
    
    for client in clients_en_base:
        emails_secondaires = client.get("emails_secondaires", [])
        print(f"   → Client {client['prenom']} {client['nom']}:")
        print(f"     Emails secondaires: {emails_secondaires}")
        
        # Vérifier si un email de la liste est dans les emails secondaires
        for email in all_emails_filtrés:
            if email in emails_secondaires:
                print(f"     ✅ TROUVÉ ! Email {email} trouvé dans emails secondaires")
                print(f"     → Client: {client['prenom']} {client['nom']}")
                client_trouvé = client
                break
        print()

# ============================================================================
# RÉSULTAT FINAL
# ============================================================================

print("=" * 80)
print("RÉSULTAT FINAL")
print("=" * 80)
if 'client_trouvé' in locals():
    print(f"✅ Client identifié: {client_trouvé['prenom']} {client_trouvé['nom']}")
    print(f"   Email principal: {client_trouvé['email_principal']}")
    print(f"   Emails secondaires: {client_trouvé.get('emails_secondaires', [])}")
    print()
    print("→ client_exists = True")
    print("→ Mistral saura que c'est un dossier existant")
else:
    print("❌ Aucun client trouvé")
    print()
    print("→ client_exists = False")
    print("→ Mistral saura que c'est probablement un NOUVEAU_DOSSIER")

print()
print("=" * 80)
print("IMPORTANT : La recherche se fait UNIQUEMENT dans Supabase")
print("=" * 80)
print("❌ PAS de nouvelle requête IMAP")
print("✅ Utilise les emails déjà extraits de l'email parsé")
print("✅ Recherche dans la table 'clients' de Supabase")
print("✅ Filtre par courtier_id pour l'isolation des données")

