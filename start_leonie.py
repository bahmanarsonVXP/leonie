#!/usr/bin/env python3
"""
Script de démarrage pour Léonie.

Ce script :
1. Vérifie/crée et active l'environnement virtuel
2. Vérifie et installe automatiquement les dépendances manquantes
3. Vérifie la disponibilité de Redis (optionnel)
4. Démarre le serveur FastAPI avec uvicorn
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple, Optional


# Couleurs pour les messages
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_success(message: str):
    """Affiche un message de succès."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")


def print_warning(message: str):
    """Affiche un message d'avertissement."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")


def print_error(message: str):
    """Affiche un message d'erreur."""
    print(f"{Colors.RED}✗{Colors.RESET} {message}")


def print_info(message: str):
    """Affiche un message d'information."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")


def print_header(message: str):
    """Affiche un en-tête."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def is_venv_active() -> bool:
    """Vérifie si un environnement virtuel est actif."""
    return (
        hasattr(sys, "real_prefix")
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        or os.environ.get("VIRTUAL_ENV") is not None
    )


def get_venv_path() -> Path:
    """Retourne le chemin de l'environnement virtuel."""
    project_root = Path(__file__).parent
    return project_root / "venv"


def venv_exists() -> bool:
    """Vérifie si l'environnement virtuel existe."""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return (venv_path / "Scripts" / "python.exe").exists()
    else:
        return (venv_path / "bin" / "python").exists()


def create_venv() -> bool:
    """Crée l'environnement virtuel."""
    venv_path = get_venv_path()
    print_info(f"Création de l'environnement virtuel dans {venv_path}...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
        )
        print_success("Environnement virtuel créé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erreur lors de la création du venv: {e}")
        return False


def get_venv_python() -> Optional[Path]:
    """Retourne le chemin du Python du venv."""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"
    
    return python_path if python_path.exists() else None


def parse_requirements() -> List[Tuple[str, Optional[str]]]:
    """
    Parse le fichier requirements.txt.
    
    Returns:
        Liste de tuples (package_name, version_spec)
    """
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print_error(f"Fichier {requirements_file} introuvable")
        return []
    
    packages = []
    with open(requirements_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Ignorer les commentaires et lignes vides
            if not line or line.startswith("#"):
                continue
            
            # Extraire le nom du package (avant >=, ==, etc.)
            if ">=" in line:
                package_name = line.split(">=")[0].strip()
                version = line.split(">=")[1].strip()
            elif "==" in line:
                package_name = line.split("==")[0].strip()
                version = line.split("==")[1].strip()
            elif ">" in line:
                package_name = line.split(">")[0].strip()
                version = line.split(">")[1].strip()
            else:
                package_name = line
                version = None
            
            # Ignorer les extras [standard] etc.
            if "[" in package_name:
                package_name = package_name.split("[")[0]
            
            packages.append((package_name, version))
    
    return packages


def check_package_installed(import_name: str) -> bool:
    """
    Vérifie si un package est installé en essayant de l'importer.
    
    Args:
        import_name: Nom d'import du package (ex: "google.auth", "PIL", "dateutil")
    
    Returns:
        True si le package peut être importé, False sinon
    """
    try:
        __import__(import_name)
        return True
    except ImportError:
        # Essayer avec le nom transformé (remplacer - par _)
        try:
            transformed_name = import_name.replace("-", "_")
            if transformed_name != import_name:
                __import__(transformed_name)
                return True
        except ImportError:
            pass
        
        # Essayer avec le nom original
        try:
            __import__(import_name)
            return True
        except ImportError:
            return False


def check_dependencies() -> Tuple[bool, List[str]]:
    """
    Vérifie si toutes les dépendances sont installées.
    
    Returns:
        Tuple (all_installed, missing_packages)
    """
    packages = parse_requirements()
    missing = []
    
    print_info("Vérification des dépendances...")
    
    for package_name, version in packages:
        # Noms spéciaux à mapper
        import_name = package_name.replace("-", "_")
        
        # Cas spéciaux
        if package_name == "python-dotenv":
            import_name = "dotenv"
        elif package_name == "pydantic-settings":
            import_name = "pydantic_settings"
        elif package_name == "email-validator":
            import_name = "email_validator"
        elif package_name == "email-reply-parser":
            import_name = "email_reply_parser"
        elif package_name == "python-docx":
            import_name = "docx"
        elif package_name == "python-json-logger":
            import_name = "pythonjsonlogger"
        elif package_name == "google-api-python-client":
            import_name = "googleapiclient"
        elif package_name == "google-auth":
            import_name = "google.auth"
        elif package_name == "google-auth-httplib2":
            import_name = "google_auth_httplib2"
        elif package_name == "google-auth-oauthlib":
            import_name = "google_auth_oauthlib"
        elif package_name == "Pillow":
            import_name = "PIL"
        elif package_name == "python-dateutil":
            import_name = "dateutil"
        elif package_name == "types-requests":
            import_name = "requests"
        elif package_name == "types-python-dateutil":
            import_name = "dateutil"
        
        if not check_package_installed(import_name):
            missing.append(package_name)
            print_warning(f"  {package_name} - manquant")
        else:
            print_success(f"  {package_name}")
    
    return len(missing) == 0, missing


def install_dependencies() -> bool:
    """Installe les dépendances depuis requirements.txt."""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print_error(f"Fichier {requirements_file} introuvable")
        return False
    
    print_info("Installation des dépendances...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
        )
        print_success("Dépendances installées avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Erreur lors de l'installation: {e}")
        return False


def check_redis() -> bool:
    """Vérifie si Redis est accessible."""
    try:
        import redis
        from app.config import get_settings
        
        settings = get_settings()
        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        client.ping()
        print_success("Redis est accessible")
        return True
    except ImportError:
        print_warning("Package redis non installé (optionnel)")
        return False
    except Exception as e:
        print_warning(f"Redis n'est pas accessible: {e}")
        print_info("Redis est optionnel pour le développement")
        return False


def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """Démarre le serveur FastAPI avec uvicorn."""
    print_header("Démarrage du serveur Léonie")
    
    try:
        import uvicorn
        from app.config import get_settings
        
        settings = get_settings()
        
        # Utiliser les settings pour reload et port si disponibles
        if hasattr(settings, "DEBUG"):
            reload = settings.DEBUG
        
        print_info(f"Lancement sur http://{host}:{port}")
        print_info(f"Mode reload: {'activé' if reload else 'désactivé'}")
        print_info("Documentation: http://localhost:8000/docs")
        print_info("Appuyez sur Ctrl+C pour arrêter\n")
        
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=settings.LOG_LEVEL.lower() if hasattr(settings, "LOG_LEVEL") else "info",
        )
    except ImportError:
        print_error("uvicorn n'est pas installé")
        print_info("Installation de uvicorn...")
        subprocess.run([sys.executable, "-m", "pip", "install", "uvicorn[standard]"], check=True)
        # Relancer
        start_server(host, port, reload)
    except KeyboardInterrupt:
        print_info("\nArrêt du serveur...")
    except Exception as e:
        print_error(f"Erreur lors du démarrage: {e}")
        sys.exit(1)


def restart_with_venv_python():
    """Relance le script avec le Python du venv."""
    venv_python = get_venv_python()
    if not venv_python:
        return False
    
    script_path = Path(__file__).absolute()
    print_info(f"Relance du script avec le Python du venv: {venv_python}")
    print_info("(Cela active automatiquement l'environnement virtuel)\n")
    
    try:
        # Préparer la commande
        cmd = [str(venv_python), str(script_path)] + sys.argv[1:]
        
        # Sur Windows, utiliser subprocess.Popen puis exit
        # Sur Unix, utiliser os.execv qui remplace le processus
        if platform.system() == "Windows":
            # Sur Windows, on lance le nouveau processus en arrière-plan
            # et on quitte immédiatement pour laisser le nouveau processus prendre le relais
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE if hasattr(subprocess, 'CREATE_NEW_CONSOLE') else 0)
            sys.exit(0)
        else:
            # Sur Unix/Linux/macOS, execv remplace le processus actuel
            # Cette ligne ne retourne jamais car le processus est remplacé
            os.execv(str(venv_python), cmd)
    except Exception as e:
        print_error(f"Impossible de relancer avec le venv Python: {e}")
        return False
    
    # Cette ligne ne sera jamais atteinte sur Unix (execv remplace le processus)
    # Sur Windows, on sort déjà avec sys.exit(0)
    return True


def main():
    """Fonction principale."""
    print_header("🚀 Script de démarrage Léonie")
    
    # 1. Vérifier l'environnement virtuel
    print_header("1. Vérification de l'environnement virtuel")
    
    if not is_venv_active():
        print_warning("Aucun environnement virtuel actif")
        
        if not venv_exists():
            print_info("Création de l'environnement virtuel...")
            if not create_venv():
                print_error("Impossible de créer le venv. Veuillez le créer manuellement:")
                print_info("  python -m venv venv")
                sys.exit(1)
        
        # Essayer de se relancer avec le Python du venv
        venv_python = get_venv_python()
        if venv_python:
            if restart_with_venv_python():
                # Cette ligne ne sera jamais atteinte car execv remplace le processus
                return
            else:
                # Si le relancement échoue, donner les instructions manuelles
                print_warning("Impossible de relancer automatiquement avec le venv")
                print_info("Veuillez activer l'environnement virtuel manuellement:")
                if platform.system() == "Windows":
                    print_info(f"  {get_venv_path()}\\Scripts\\activate")
                else:
                    print_info(f"  source {get_venv_path()}/bin/activate")
                print_info("\nPuis relancez ce script:")
                print_info(f"  python {Path(__file__).name}")
                sys.exit(0)
        else:
            print_error("Python du venv introuvable")
            sys.exit(1)
    else:
        venv_path = os.environ.get("VIRTUAL_ENV", sys.prefix)
        print_success(f"Environnement virtuel actif: {venv_path}")
    
    # 2. Vérifier les dépendances
    print_header("2. Vérification des dépendances")
    
    all_installed, missing = check_dependencies()
    
    if not all_installed:
        print_warning(f"{len(missing)} dépendance(s) manquante(s)")
        print_info("Installation automatique des dépendances manquantes...")
        
        if not install_dependencies():
            print_error("Échec de l'installation des dépendances")
            sys.exit(1)
        
        # Vérifier à nouveau après l'installation
        print_info("Vérification après installation...")
        all_installed, missing = check_dependencies()
        if not all_installed:
            print_error(f"Certaines dépendances n'ont pas pu être installées: {', '.join(missing)}")
            sys.exit(1)
        else:
            print_success("Toutes les dépendances sont maintenant installées")
    else:
        print_success("Toutes les dépendances sont installées")
    
    # 3. Vérifier Redis (optionnel)
    print_header("3. Vérification de Redis (optionnel)")
    check_redis()
    
    # 4. Démarrer le serveur
    print_header("4. Démarrage du serveur")
    start_server()


if __name__ == "__main__":
    main()

