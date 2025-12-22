#!/usr/bin/env python3
"""
Script de débogage pour la connexion IMAP.

Ce script aide à identifier les problèmes d'authentification IMAP
en affichant des informations détaillées sur la configuration et les erreurs.
"""

import imaplib
import os
import sys
from pathlib import Path

# Couleurs pour les messages
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_success(message: str):
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def print_error(message: str):
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def print_info(message: str):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")


def print_header(message: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def check_env_file():
    """Vérifie si le fichier .env existe et affiche les variables IMAP."""
    print_header("1. Vérification du fichier .env")
    
    env_path = Path(".env")
    if not env_path.exists():
        print_error("Fichier .env introuvable")
        print_info("Créez un fichier .env à la racine du projet")
        return False
    
    print_success(f"Fichier .env trouvé: {env_path.absolute()}")
    
    # Lire les variables IMAP depuis .env
    imap_vars = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                
                if key.startswith("IMAP_"):
                    imap_vars[key] = value
    
    print_info("Variables IMAP trouvées dans .env:")
    for key in ["IMAP_HOST", "IMAP_PORT", "IMAP_EMAIL", "IMAP_LABEL"]:
        if key in imap_vars:
            print(f"  {key} = {imap_vars[key]}")
        else:
            print_warning(f"  {key} = NON DÉFINI")
    
    # Pour le mot de passe, on affiche seulement la longueur
    if "IMAP_PASSWORD" in imap_vars:
        pwd_len = len(imap_vars["IMAP_PASSWORD"])
        has_spaces = " " in imap_vars["IMAP_PASSWORD"]
        print(f"  IMAP_PASSWORD = {'*' * min(pwd_len, 20)} (longueur: {pwd_len}, espaces: {has_spaces})")
    else:
        print_warning("  IMAP_PASSWORD = NON DÉFINI")
    
    return True


def check_settings():
    """Vérifie les settings chargés par l'application."""
    print_header("2. Vérification des settings de l'application")
    
    try:
        from app.config import get_settings
        
        settings = get_settings()
        
        print_success("Settings chargés avec succès")
        print_info(f"IMAP_HOST: {settings.IMAP_HOST}")
        print_info(f"IMAP_PORT: {settings.IMAP_PORT}")
        print_info(f"IMAP_EMAIL: {settings.IMAP_EMAIL}")
        print_info(f"IMAP_LABEL: {settings.IMAP_LABEL}")
        
        pwd_len = len(settings.IMAP_PASSWORD)
        has_spaces = " " in settings.IMAP_PASSWORD
        print_info(f"IMAP_PASSWORD: {'*' * min(pwd_len, 20)} (longueur: {pwd_len}, espaces: {has_spaces})")
        
        return settings
        
    except Exception as e:
        print_error(f"Erreur lors du chargement des settings: {e}")
        print_info("Vérifiez que toutes les variables requises sont dans .env")
        return None


def test_imap_connection(settings):
    """Teste la connexion IMAP avec détails."""
    print_header("3. Test de connexion IMAP")
    
    if not settings:
        print_error("Impossible de tester sans settings")
        return False
    
    print_info(f"Connexion à {settings.IMAP_HOST}:{settings.IMAP_PORT}")
    
    try:
        # Test de connexion SSL
        print_info("Étape 1: Connexion SSL au serveur...")
        imap = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        print_success("Connexion SSL réussie")
        
        # Test d'authentification
        print_info("Étape 2: Authentification...")
        print_info(f"  Email: {settings.IMAP_EMAIL}")
        print_info(f"  Mot de passe: {'*' * min(len(settings.IMAP_PASSWORD), 20)}")
        
        # Vérifier si le mot de passe contient des espaces (App Password Gmail)
        if " " in settings.IMAP_PASSWORD:
            print_warning("Le mot de passe contient des espaces (normal pour App Password Gmail)")
            print_info("Assurez-vous que les espaces sont bien préservés dans .env")
        
        imap.login(settings.IMAP_EMAIL, settings.IMAP_PASSWORD)
        print_success("Authentification réussie !")
        
        # Test de sélection du dossier
        print_info("Étape 3: Sélection du dossier/label...")
        print_info(f"  Label: {settings.IMAP_LABEL}")
        
        status, messages = imap.select(settings.IMAP_LABEL, readonly=True)
        if status == "OK":
            print_success(f"Dossier '{settings.IMAP_LABEL}' sélectionné avec succès")
            
            # Compter les emails
            status, message_numbers = imap.search(None, "ALL")
            if status == "OK":
                num_emails = len(message_numbers[0].split()) if message_numbers[0] else 0
                print_info(f"Nombre total d'emails dans '{settings.IMAP_LABEL}': {num_emails}")
        else:
            print_warning(f"Impossible de sélectionner le dossier '{settings.IMAP_LABEL}'")
            print_info("Vérifiez que le label existe dans Gmail")
            print_info("Essayez avec 'INBOX' si le label personnalisé n'existe pas")
        
        # Fermeture
        imap.close()
        imap.logout()
        print_success("Connexion fermée proprement")
        
        return True
        
    except imaplib.IMAP4.error as e:
        error_msg = str(e)
        print_error(f"Erreur d'authentification IMAP: {error_msg}")
        
        # Messages d'aide selon l'erreur
        if "AUTHENTICATE failed" in error_msg or "LOGIN failed" in error_msg:
            print_warning("\nCauses possibles:")
            print_info("1. Mot de passe incorrect")
            print_info("2. Pour Gmail, vous devez utiliser un App Password (pas le mot de passe principal)")
            print_info("3. L'authentification à 2 facteurs doit être activée sur le compte Gmail")
            print_info("4. Vérifiez que les espaces dans l'App Password sont bien préservés")
        elif "invalid credentials" in error_msg.lower():
            print_warning("Identifiants invalides")
            print_info("Vérifiez IMAP_EMAIL et IMAP_PASSWORD dans .env")
        else:
            print_warning(f"Erreur IMAP: {error_msg}")
        
        return False
        
    except Exception as e:
        print_error(f"Erreur de connexion: {e}")
        print_warning(f"Type d'erreur: {type(e).__name__}")
        return False


def check_gmail_app_password():
    """Affiche des instructions pour créer un App Password Gmail."""
    print_header("4. Instructions App Password Gmail")
    
    print_info("Pour Gmail, vous devez utiliser un App Password:")
    print_info("")
    print_info("1. Allez sur https://myaccount.google.com/security")
    print_info("2. Activez l'authentification à 2 facteurs (obligatoire)")
    print_info("3. Allez dans 'Mots de passe des applications'")
    print_info("4. Créez un nouveau mot de passe pour 'Léonie'")
    print_info("5. Copiez le mot de passe généré (format: xxxx xxxx xxxx xxxx)")
    print_info("6. Collez-le dans .env comme valeur de IMAP_PASSWORD")
    print_info("")
    print_warning("Important: Conservez les espaces dans le mot de passe !")
    print_warning("Le format doit être: IMAP_PASSWORD=\"xxxx xxxx xxxx xxxx\"")


def main():
    """Fonction principale."""
    print_header("🔍 Script de débogage IMAP pour Léonie")
    
    # 1. Vérifier .env
    if not check_env_file():
        print_error("Impossible de continuer sans fichier .env")
        sys.exit(1)
    
    # 2. Vérifier les settings
    settings = check_settings()
    if not settings:
        print_error("Impossible de charger les settings")
        sys.exit(1)
    
    # 3. Tester la connexion
    success = test_imap_connection(settings)
    
    # 4. Afficher les instructions si échec
    if not success:
        check_gmail_app_password()
        print_header("Résumé")
        print_error("La connexion IMAP a échoué")
        print_info("Vérifiez:")
        print_info("  - Que IMAP_EMAIL est correct")
        print_info("  - Que IMAP_PASSWORD est un App Password Gmail valide")
        print_info("  - Que l'authentification à 2 facteurs est activée")
        print_info("  - Que les espaces dans l'App Password sont préservés")
        sys.exit(1)
    else:
        print_header("Résumé")
        print_success("Tous les tests sont passés ! La connexion IMAP fonctionne.")
        print_info("Vous pouvez maintenant utiliser l'endpoint /test-imap")


if __name__ == "__main__":
    main()

