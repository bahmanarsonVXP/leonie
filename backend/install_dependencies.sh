#!/bin/bash
# ==============================================================================
# Installation des dépendances système pour Léonie
# ==============================================================================
# Script d'installation des dépendances système nécessaires au traitement
# de documents (LibreOffice, Ghostscript, Poppler).
#
# Usage:
#   chmod +x install_dependencies.sh
#   ./install_dependencies.sh
#
# Utilisé dans:
#   - Dockerfile pour Railway
#   - Installation locale
#   - CI/CD
# ==============================================================================

set -e  # Arrêter en cas d'erreur

echo "=============================================================="
echo "Installation des dépendances système pour Léonie"
echo "=============================================================="

# Détecter l'OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "OS détecté: Linux (Debian/Ubuntu)"

    # Mettre à jour les packages
    echo "Mise à jour des packages..."
    apt-get update -y

    # Installation LibreOffice
    echo "Installation de LibreOffice..."
    apt-get install -y \
        libreoffice \
        libreoffice-writer \
        libreoffice-calc \
        libreoffice-impress \
        --no-install-recommends

    # Installation Ghostscript
    echo "Installation de Ghostscript..."
    apt-get install -y ghostscript

    # Installation Poppler (pour pdf2image)
    echo "Installation de Poppler..."
    apt-get install -y poppler-utils

    # Nettoyage pour réduire la taille de l'image Docker
    echo "Nettoyage des fichiers temporaires..."
    apt-get clean
    rm -rf /var/lib/apt/lists/*

    echo "✅ Toutes les dépendances ont été installées avec succès (Linux)"

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "OS détecté: macOS"

    # Vérifier que Homebrew est installé
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew n'est pas installé. Installer depuis https://brew.sh"
        exit 1
    fi

    # Installation LibreOffice
    echo "Installation de LibreOffice..."
    brew install --cask libreoffice || echo "LibreOffice déjà installé"

    # Installation Ghostscript
    echo "Installation de Ghostscript..."
    brew install ghostscript || echo "Ghostscript déjà installé"

    # Installation Poppler
    echo "Installation de Poppler..."
    brew install poppler || echo "Poppler déjà installé"

    echo "✅ Toutes les dépendances ont été installées avec succès (macOS)"

else
    echo "❌ OS non supporté: $OSTYPE"
    echo "Ce script supporte uniquement Linux (Debian/Ubuntu) et macOS"
    exit 1
fi

# Vérification des installations
echo ""
echo "=============================================================="
echo "Vérification des installations..."
echo "=============================================================="

# Vérifier LibreOffice
if command -v libreoffice &> /dev/null || [ -f "/Applications/LibreOffice.app/Contents/MacOS/soffice" ]; then
    LIBREOFFICE_VERSION=$(libreoffice --version 2>/dev/null || /Applications/LibreOffice.app/Contents/MacOS/soffice --version 2>/dev/null || echo "version inconnue")
    echo "✅ LibreOffice: $LIBREOFFICE_VERSION"
else
    echo "❌ LibreOffice non trouvé"
fi

# Vérifier Ghostscript
if command -v gs &> /dev/null; then
    GS_VERSION=$(gs --version)
    echo "✅ Ghostscript: version $GS_VERSION"
else
    echo "❌ Ghostscript non trouvé"
fi

# Vérifier Poppler (pdfinfo)
if command -v pdfinfo &> /dev/null; then
    POPPLER_VERSION=$(pdfinfo -v 2>&1 | head -n 1 || echo "version inconnue")
    echo "✅ Poppler: $POPPLER_VERSION"
else
    echo "❌ Poppler non trouvé"
fi

echo ""
echo "=============================================================="
echo "Installation terminée !"
echo "=============================================================="
echo ""
echo "Prochaines étapes:"
echo "1. Installer les dépendances Python: pip install -r requirements.txt"
echo "2. Configurer le fichier .env"
echo "3. Lancer l'application: uvicorn main:app --reload"
echo ""
