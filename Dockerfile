# ==============================================================================
# Dockerfile pour Léonie - Agent IA pour courtiers en prêts
# ==============================================================================
# Image optimisée pour Railway avec toutes les dépendances système
# pour le traitement de documents (LibreOffice, Ghostscript, Poppler)
# ==============================================================================
# Ce Dockerfile est à la racine du monorepo et construit le backend
# ==============================================================================

FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Léonie Team"
LABEL description="Agent IA pour courtiers en prêts immobiliers"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Créer un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 leonie && \
    mkdir -p /app /tmp/leonie && \
    chown -R leonie:leonie /app /tmp/leonie

# Définir le répertoire de travail
WORKDIR /app

# Installation des dépendances système
# Note: Exécuté en tant que root pour apt-get
COPY backend/install_dependencies.sh /tmp/install_dependencies.sh
RUN chmod +x /tmp/install_dependencies.sh && \
    /tmp/install_dependencies.sh && \
    rm /tmp/install_dependencies.sh

# Copier les fichiers de dépendances Python depuis backend/
COPY --chown=leonie:leonie backend/requirements.txt .

# Installer les dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copier le code de l'application depuis backend/
COPY --chown=leonie:leonie backend/ .

# Copier et rendre exécutable le script de démarrage
COPY --chown=leonie:leonie backend/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Passer à l'utilisateur non-root
USER leonie

# Exposer le port (Railway définit PORT via variable d'environnement)
EXPOSE 8000

# Healthcheck pour Railway
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD python -c "import os, requests; port = os.getenv('PORT', '8000'); requests.get(f'http://localhost:{port}/health', timeout=5)"

# Commande de démarrage
# Railway définit PORT automatiquement via variable d'environnement
CMD ["/app/start.sh"]

