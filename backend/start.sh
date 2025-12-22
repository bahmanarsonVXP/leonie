#!/bin/bash
# Script de démarrage pour Railway
# Lit PORT depuis l'environnement et lance uvicorn

PORT=${PORT:-8000}
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"

