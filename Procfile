# ==============================================================================
# Procfile pour Railway
# ==============================================================================
# Définit les processus à lancer sur Railway
# ==============================================================================

# Processus web (FastAPI)
web: uvicorn main:app --host 0.0.0.0 --port $PORT

# Processus worker (Redis Queue)
# Décommenter quand les workers seront implémentés
# worker: rq worker high default --with-scheduler
