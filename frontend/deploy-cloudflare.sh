#!/bin/bash

# ==============================================================================
# LÉONIE FRONTEND - Déploiement Cloudflare Pages via CLI
# ==============================================================================

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🚀 DÉPLOIEMENT CLOUDFLARE PAGES"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Vérifier que wrangler est installé
if ! command -v wrangler &> /dev/null; then
    echo -e "${RED}❌ Wrangler n'est pas installé${NC}"
    echo ""
    echo "Installez-le avec :"
    echo "  npm install -g wrangler"
    exit 1
fi

# Vérifier l'authentification
echo -e "${BLUE}[INFO]${NC} Vérification de l'authentification..."
if ! wrangler whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Pas authentifié${NC}"
    echo ""
    echo "Authentifiez-vous avec :"
    echo "  wrangler login"
    exit 1
fi

echo -e "${GREEN}✓${NC} Authentifié à Cloudflare"
echo ""

# Vérifier qu'on est dans le dossier frontend
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ Ce script doit être exécuté depuis le dossier frontend/${NC}"
    exit 1
fi

# Build le projet
echo -e "${BLUE}[INFO]${NC} Build du projet..."
npm run build

if [ ! -d "dist" ]; then
    echo -e "${RED}❌ Le dossier dist/ n'a pas été créé${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Build réussi"
echo ""

# Déployer sur Cloudflare Pages
echo -e "${BLUE}[INFO]${NC} Déploiement vers Cloudflare Pages..."
echo ""

# Si premier déploiement, créer le projet
if ! wrangler pages project list 2>/dev/null | grep -q "leonie"; then
    echo -e "${YELLOW}[INFO]${NC} Création du projet leonie..."
    wrangler pages project create leonie --production-branch=main
fi

# Déployer
wrangler pages deploy dist --project-name=leonie --commit-dirty=true

echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "  ${GREEN}✅ DÉPLOIEMENT TERMINÉ !${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "${YELLOW}⚠️  N'oubliez pas de configurer les variables d'environnement :${NC}"
echo ""
echo "  wrangler pages secret put VITE_SUPABASE_URL --project-name=leonie"
echo "  wrangler pages secret put VITE_SUPABASE_ANON_KEY --project-name=leonie"
echo "  wrangler pages secret put VITE_API_URL --project-name=leonie"
echo ""
echo "Ou via le Dashboard : https://dash.cloudflare.com/"
echo ""
