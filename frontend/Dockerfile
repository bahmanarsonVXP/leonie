# ==============================================================================
# LÉONIE FRONTEND - Dockerfile
# ==============================================================================

FROM node:18-alpine

# Installer curl pour healthcheck
RUN apk add --no-cache curl

# Créer dossier app
WORKDIR /app

# Copier package files
COPY package*.json ./

# Installer dépendances
RUN npm ci

# Copier le code
COPY . .

# Exposer le port
EXPOSE 3000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Commande par défaut (dev)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
