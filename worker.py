"""
Worker RQ pour exécuter les background jobs.

Ce script lance un worker qui consomme les queues Redis ("high" et "default")
et exécute les jobs de manière asynchrone.

Usage:
    python worker.py

    Ou avec plusieurs workers en parallèle:
    rq worker high default --with-scheduler

Note:
    - Le worker "high" a priorité sur "default"
    - Les jobs sont exécutés de manière séquentielle dans chaque worker
    - Plusieurs workers peuvent tourner en parallèle pour scalabilité
    - Sur macOS: utilise SimpleWorker pour éviter les problèmes de fork()
"""

import os
import sys
import platform
from rq import Worker, SimpleWorker

from app.utils.redis_client import redis_conn, queue_high, queue_default

# Fix pour macOS: désactiver la sécurité fork() qui cause des crashes
# avec les bibliothèques C (Google API, etc.)
if platform.system() == "Darwin":  # macOS
    os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

if __name__ == '__main__':
    # Lancer worker qui consomme les 2 queues
    # Priorité : high d'abord, puis default

    # Sur macOS, utiliser SimpleWorker (pas de fork) pour éviter les crashes
    # En production Linux/Docker, Worker standard avec fork est plus performant
    WorkerClass = SimpleWorker if platform.system() == "Darwin" else Worker

    worker = WorkerClass(
        [queue_high, queue_default],
        connection=redis_conn
    )

    print("=" * 70)
    print(f"🚀 Léonie Worker RQ démarré ({'SimpleWorker - macOS' if platform.system() == 'Darwin' else 'Worker - fork mode'})")
    print("=" * 70)
    print(f"📋 Queues surveillées (par ordre de priorité):")
    for i, q in enumerate(worker.queues, 1):
        print(f"   {i}. {q.name}")
    print(f"🔗 Redis: {redis_conn.connection_pool.connection_kwargs.get('host')}:{redis_conn.connection_pool.connection_kwargs.get('port')}")
    print("=" * 70)
    print("En attente de jobs...\n")

    try:
        # Démarrer le worker (bloquant)
        worker.work()
    except KeyboardInterrupt:
        print("\n\n👋 Worker arrêté par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale du worker: {e}")
        sys.exit(1)
