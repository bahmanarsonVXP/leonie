"""
Test pour vérifier que le worker peut traiter les nouveaux jobs.
"""
import asyncio
from app.cron.check_emails import check_new_emails

print("🔍 Récupération et traitement des nouveaux emails...")
print("=" * 70)

# Lance le check des emails qui va:
# 1. Récupérer les emails
# 2. Identifier courtiers et clients
# 3. Classifier avec Mistral
# 4. Enqueuer les jobs
asyncio.run(check_new_emails())

print("\n✅ Terminé!")
print("\nVérification des jobs dans Redis:")
import subprocess
high_count = subprocess.check_output(['redis-cli', 'LLEN', 'rq:queue:high']).decode().strip()
default_count = subprocess.check_output(['redis-cli', 'LLEN', 'rq:queue:default']).decode().strip()

print(f"  - Queue 'high': {high_count} job(s)")
print(f"  - Queue 'default': {default_count} job(s)")
print("\n👀 Surveillez les logs du worker pour voir l'exécution des jobs.")
print("   tail -f /tmp/worker_fixed.log")
