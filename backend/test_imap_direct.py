#!/usr/bin/env python3
"""
Test direct de connexion IMAP pour identifier le problème.

Ce script teste différentes configurations pour identifier
le problème d'authentification.
"""

import imaplib
import sys
from app.config import get_settings

def test_imap_with_email(email, password):
    """Teste la connexion IMAP avec un email et mot de passe spécifiques."""
    print(f"\n{'='*60}")
    print(f"Test avec email: {email}")
    print(f"{'='*60}\n")
    
    try:
        # Connexion
        print("1. Connexion SSL...")
        imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        print("   ✓ Connexion SSL réussie")
        
        # Authentification
        print("2. Authentification...")
        print(f"   Email: {email}")
        print(f"   Password: {'*' * len(password)} (longueur: {len(password)})")
        imap.login(email, password)
        print("   ✓ Authentification réussie !")
        
        # Test INBOX
        print("3. Test sélection INBOX...")
        status, messages = imap.select("INBOX", readonly=True)
        if status == "OK":
            print("   ✓ INBOX accessible")
            
            # Compter les emails
            status, message_numbers = imap.search(None, "ALL")
            if status == "OK":
                num_emails = len(message_numbers[0].split()) if message_numbers[0] else 0
                print(f"   ✓ Nombre d'emails dans INBOX: {num_emails}")
        else:
            print(f"   ✗ Impossible de sélectionner INBOX: {status}")
        
        # Fermeture
        imap.close()
        imap.logout()
        print("   ✓ Connexion fermée")
        
        return True
        
    except imaplib.IMAP4.error as e:
        error_msg = str(e)
        print(f"   ✗ Erreur IMAP: {error_msg}")
        
        if "AUTHENTICATE failed" in error_msg or "Invalid credentials" in error_msg:
            print("\n   💡 Suggestions:")
            print("      - Vérifiez que l'email est le compte Gmail PRINCIPAL (pas un alias)")
            print("      - Vérifiez que l'App Password a été créé pour ce compte")
            print("      - Essayez de créer un nouvel App Password")
            print("      - Vérifiez que l'authentification à 2 facteurs est activée")
        
        return False
    except Exception as e:
        print(f"   ✗ Erreur: {e}")
        return False


def main():
    """Fonction principale."""
    print("="*60)
    print("Test de connexion IMAP - Diagnostic avancé")
    print("="*60)
    
    settings = get_settings()
    
    # Test 1: Avec l'email configuré
    print("\n" + "="*60)
    print("TEST 1: Avec l'email configuré dans .env")
    print("="*60)
    success1 = test_imap_with_email(settings.IMAP_EMAIL, settings.IMAP_PASSWORD)
    
    if not success1:
        print("\n" + "="*60)
        print("DIAGNOSTIC")
        print("="*60)
        print("\n⚠️  L'authentification a échoué avec l'email configuré.")
        print("\nCauses possibles :")
        print("1. L'email 'leonie@voxperience.com' est un ALIAS Gmail")
        print("   → Les App Passwords doivent utiliser l'email PRINCIPAL du compte Gmail")
        print("   → Exemple: si votre compte principal est 'votre.nom@gmail.com',")
        print("     utilisez cet email au lieu de l'alias")
        print("\n2. L'App Password a été créé pour un autre compte")
        print("   → Vérifiez dans Google Account > Sécurité > Mots de passe des applications")
        print("\n3. L'App Password n'est pas encore actif")
        print("   → Attendez quelques minutes après la création")
        print("\n4. L'authentification à 2 facteurs n'est pas activée")
        print("   → Activez-la dans Google Account > Sécurité")
        
        print("\n" + "="*60)
        print("SOLUTION RECOMMANDÉE")
        print("="*60)
        print("\n1. Identifiez votre email Gmail PRINCIPAL (celui avec lequel vous vous connectez)")
        print("2. Créez un App Password pour ce compte principal")
        print("3. Mettez à jour .env avec :")
        print(f"   IMAP_EMAIL=votre.email.principal@gmail.com")
        print(f"   IMAP_PASSWORD=\"xxxx xxxx xxxx xxxx\"")
        print("\n4. Relancez ce script pour tester")
    else:
        print("\n" + "="*60)
        print("SUCCÈS !")
        print("="*60)
        print("\n✓ La connexion IMAP fonctionne avec l'email configuré.")
        print("Le problème pourrait être avec le label 'LEONIE'.")
        print("Essayez de changer IMAP_LABEL=INBOX dans .env")


if __name__ == "__main__":
    main()

