#!/bin/bash
# Script de test pour la version Railway de Léonie
# Usage: ./test_railway.sh https://votre-app.up.railway.app

set -e

# Couleurs pour l'output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Vérifier que l'URL est fournie
if [ -z "$1" ]; then
    echo -e "${RED}❌ Erreur: URL Railway non fournie${NC}"
    echo "Usage: ./test_railway.sh https://votre-app.up.railway.app"
    exit 1
fi

RAILWAY_URL="$1"
echo -e "${BLUE}🚀 Test de l'application Léonie sur Railway${NC}"
echo -e "${BLUE}URL: ${RAILWAY_URL}${NC}\n"

# Fonction pour tester un endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    
    echo -e "${YELLOW}📡 Test: ${description}${NC}"
    echo -e "   ${method} ${endpoint}"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "${RAILWAY_URL}${endpoint}")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "${RAILWAY_URL}${endpoint}")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✅ Succès (HTTP ${http_code})${NC}"
        if command -v jq &> /dev/null; then
            echo "$body" | jq '.' 2>/dev/null || echo "$body"
        else
            echo "$body"
        fi
        echo ""
        return 0
    else
        echo -e "${RED}❌ Erreur (HTTP ${http_code})${NC}"
        echo "$body"
        echo ""
        return 1
    fi
}

# Tests
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}1. Test de santé (Health Check)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
test_endpoint "GET" "/health" "Health check"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}2. Test de la route racine${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
test_endpoint "GET" "/" "Route racine"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}3. Test Google Drive (création dossier + upload)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
test_endpoint "POST" "/test-drive" "Test Google Drive"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}4. Test IMAP (connexion email)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
test_endpoint "GET" "/test-imap" "Test IMAP"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Tous les tests terminés!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

