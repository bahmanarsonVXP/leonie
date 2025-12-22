#!/bin/bash

# ==============================================================================
# LÉONIE - Script de Démarrage Rapide
# ==============================================================================
# Lance automatiquement backend et frontend en local
# Usage: ./start.sh
# Arrêter: Ctrl+C
# ==============================================================================

set -e

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Fonction de cleanup à l'arrêt
cleanup() {
    log_info "Arrêt des serveurs..."

    # Tuer les processus enfants
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        log_info "Backend arrêté (PID: $BACKEND_PID)"
    fi

    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        log_info "Frontend arrêté (PID: $FRONTEND_PID)"
    fi

    log_success "Serveurs arrêtés proprement ✓"
    exit 0
}

# Capturer Ctrl+C
trap cleanup SIGINT SIGTERM

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  🚀 LÉONIE - Démarrage des serveurs locaux"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Vérifier que nous sommes à la racine du projet
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    log_error "Ce script doit être exécuté depuis la racine du monorepo Léonie"
    log_error "Structure attendue: leonie/backend/ et leonie/frontend/"
    exit 1
fi

# ==============================================================================
# VÉRIFICATIONS PRÉ-DÉMARRAGE
# ==============================================================================

log_info "Vérification des prérequis..."

# Nettoyer les anciens processus sur les ports 8000 et 3000
log_info "Vérification des ports..."

# Port 8000 (backend)
if lsof -i :8000 > /dev/null 2>&1; then
    log_warning "Port 8000 déjà utilisé, nettoyage en cours..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Port 3000 (frontend)
if lsof -i :3000 > /dev/null 2>&1; then
    log_warning "Port 3000 déjà utilisé, nettoyage en cours..."
    lsof -ti :3000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

log_success "Ports 8000 et 3000 libres ✓"

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 n'est pas installé"
    exit 1
fi

# Vérifier Node.js
if ! command -v node &> /dev/null; then
    log_error "Node.js n'est pas installé"
    exit 1
fi

# Vérifier venv backend
if [ ! -d "backend/venv" ]; then
    log_warning "Environnement virtuel Python non trouvé"
    log_info "Création de l'environnement virtuel..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    log_success "Environnement virtuel créé ✓"
fi

# Vérifier node_modules frontend
if [ ! -d "frontend/node_modules" ]; then
    log_warning "node_modules non trouvé"
    log_info "Installation des dépendances frontend..."
    cd frontend
    npm install
    cd ..
    log_success "Dépendances installées ✓"
fi

# Vérifier .env backend
if [ ! -f "backend/.env" ]; then
    log_error "Fichier backend/.env manquant"
    log_info "Copiez backend/.env.example vers backend/.env et configurez-le"
    exit 1
fi

# Vérifier .env.local frontend
if [ ! -f "frontend/.env.local" ]; then
    log_warning "Fichier frontend/.env.local manquant"
    log_info "Copie de .env.example vers .env.local..."
    cp frontend/.env.example frontend/.env.local
    log_warning "⚠️  Pensez à configurer frontend/.env.local avec vos credentials Supabase"
fi

log_success "Prérequis vérifiés ✓"
echo ""

# ==============================================================================
# DÉMARRAGE BACKEND
# ==============================================================================

log_info "Démarrage du backend Python (FastAPI)..."

cd backend
source venv/bin/activate

# Lancer backend en arrière-plan
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!

cd ..

# Attendre que le backend soit prêt
log_info "Attente du démarrage du backend..."
sleep 3

# Vérifier que le backend est accessible
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    log_success "✓ Backend démarré sur http://localhost:8000"
    log_info "  - API Docs: http://localhost:8000/docs"
    log_info "  - Logs: tail -f backend.log"
else
    log_warning "Le backend tarde à démarrer (vérifier backend.log)"
fi

echo ""

# ==============================================================================
# DÉMARRAGE FRONTEND
# ==============================================================================

log_info "Démarrage du frontend React (Vite)..."

cd frontend

# Lancer frontend en arrière-plan
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!

cd ..

# Attendre que le frontend soit prêt
log_info "Attente du démarrage du frontend..."
sleep 5

# Vérifier que le frontend est accessible
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    log_success "✓ Frontend démarré sur http://localhost:3000"
    log_info "  - Logs: tail -f frontend.log"
else
    log_warning "Le frontend tarde à démarrer (vérifier frontend.log)"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ LÉONIE EST PRÊT !"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "  🌐 Frontend : ${GREEN}http://localhost:3000${NC}"
echo "  🔌 Backend  : ${GREEN}http://localhost:8000${NC}"
echo "  📚 API Docs : ${BLUE}http://localhost:8000/docs${NC}"
echo ""
echo "  📋 Logs:"
echo "     - Backend  : tail -f backend.log"
echo "     - Frontend : tail -f frontend.log"
echo ""
echo "  🛑 Arrêter   : ${YELLOW}Ctrl+C${NC}"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

# Attendre indéfiniment (les serveurs tournent en arrière-plan)
wait
