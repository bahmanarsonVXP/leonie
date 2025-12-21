#!/bin/bash
# ==============================================================================
# Script de déploiement Railway pour Léonie
# ==============================================================================
# Ce script vous guide pour déployer Léonie sur Railway.
# Usage: ./deploy-railway.sh
# ==============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  Déploiement Léonie sur Railway                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# 1. Vérifications préalables
# ==============================================================================

echo -e "${BLUE}[1/5] Vérification des prérequis...${NC}"

# Vérifier que Railway CLI est installé
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI n'est pas installé${NC}"
    echo ""
    echo "Installez-le avec:"
    echo "  npm install -g @railway/cli"
    echo "ou"
    echo "  brew install railway"
    exit 1
fi

echo -e "${GREEN}✅ Railway CLI installé: $(railway --version)${NC}"

# Vérifier que l'utilisateur est authentifié
if ! railway whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Vous n'êtes pas authentifié sur Railway${NC}"
    echo ""
    echo "Authentifiez-vous avec:"
    read -p "Voulez-vous vous authentifier maintenant? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        railway login
    else
        echo -e "${RED}Déploiement annulé${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Authentifié: $(railway whoami)${NC}"

# Vérifier que les fichiers essentiels existent
echo ""
echo -e "${BLUE}[2/5] Vérification des fichiers...${NC}"

REQUIRED_FILES=(
    "Dockerfile"
    ".dockerignore"
    "requirements.txt"
    "main.py"
    "install_dependencies.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Fichier manquant: $file${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ $file${NC}"
done

# ==============================================================================
# 2. Initialiser ou lier le projet
# ==============================================================================

echo ""
echo -e "${BLUE}[3/5] Configuration du projet Railway...${NC}"

# Vérifier si déjà lié à un projet
if [ -f ".railway/project.json" ]; then
    echo -e "${GREEN}✅ Projet déjà lié${NC}"
    PROJECT_ID=$(cat .railway/project.json | grep -o '"projectId":"[^"]*' | cut -d'"' -f4)
    echo "   Project ID: $PROJECT_ID"
else
    echo -e "${YELLOW}⚠️  Aucun projet Railway lié${NC}"
    echo ""
    echo "Choisissez une option:"
    echo "  1) Créer un nouveau projet"
    echo "  2) Lier à un projet existant"
    echo "  3) Annuler"
    read -p "Votre choix (1-3): " choice

    case $choice in
        1)
            echo "Nom du projet Railway:"
            read -p "> " project_name
            railway init --name "$project_name"
            ;;
        2)
            railway link
            ;;
        3)
            echo -e "${RED}Déploiement annulé${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Choix invalide${NC}"
            exit 1
            ;;
    esac
fi

# ==============================================================================
# 3. Configurer les variables d'environnement
# ==============================================================================

echo ""
echo -e "${BLUE}[4/5] Variables d'environnement...${NC}"

# Compter les variables configurées
VAR_COUNT=$(railway variables --json 2>/dev/null | grep -c '"' || echo "0")

if [ "$VAR_COUNT" -lt 5 ]; then
    echo -e "${YELLOW}⚠️  Peu de variables d'environnement configurées ($VAR_COUNT)${NC}"
    echo ""
    echo "Variables REQUISES (voir .env.example):"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_KEY"
    echo "  - MISTRAL_API_KEY"
    echo "  - IMAP_EMAIL"
    echo "  - IMAP_PASSWORD (App Password Gmail)"
    echo "  - SMTP_EMAIL"
    echo "  - SMTP_PASSWORD"
    echo "  - API_SECRET_KEY (générer avec: openssl rand -hex 32)"
    echo ""
    echo "Configurez-les avec:"
    echo "  railway variables set NOM_VARIABLE=\"valeur\""
    echo ""
    echo "Ou via le dashboard:"
    echo "  railway open"
    echo ""
    read -p "Voulez-vous ouvrir le dashboard maintenant pour configurer? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        railway open
        echo ""
        echo "Configurez les variables, puis relancez ce script."
        exit 0
    else
        read -p "Continuer quand même? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}Déploiement annulé${NC}"
            exit 0
        fi
    fi
else
    echo -e "${GREEN}✅ $VAR_COUNT variable(s) configurée(s)${NC}"
fi

# ==============================================================================
# 4. Déployer
# ==============================================================================

echo ""
echo -e "${BLUE}[5/5] Déploiement sur Railway...${NC}"
echo ""
echo "Le déploiement va:"
echo "  1. Builder l'image Docker (~5-10 minutes)"
echo "  2. Installer LibreOffice, Ghostscript, Poppler"
echo "  3. Installer les dépendances Python"
echo "  4. Démarrer l'application"
echo ""
read -p "Lancer le déploiement maintenant? (y/n) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Déploiement annulé${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}🚀 Lancement du déploiement...${NC}"
echo ""

# Déployer
railway up --detach

echo ""
echo -e "${GREEN}✅ Déploiement lancé!${NC}"
echo ""
echo "Commandes utiles:"
echo "  - Voir les logs:     railway logs"
echo "  - Voir l'URL:        railway domain"
echo "  - Ouvrir dashboard:  railway open"
echo "  - Voir variables:    railway variables"
echo ""
echo "Une fois déployé, testez:"
echo "  curl https://votre-app.railway.app/health"
echo ""

# Proposer de voir les logs
read -p "Voulez-vous suivre les logs maintenant? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Logs en temps réel (Ctrl+C pour quitter):"
    echo "═══════════════════════════════════════════════════════════"
    railway logs --tail
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Déploiement terminé! 🎉                                           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════╝${NC}"
