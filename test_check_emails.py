"""
Script de test pour exécuter check_emails manuellement.
"""

import asyncio
import sys
from app.cron.check_emails import check_new_emails

async def main():
    print("🔍 Test de récupération des emails...")
    print("=" * 70)
    
    try:
        stats = await check_new_emails()
        print("\n✅ Terminé!")
        print(f"Statistiques: {stats}")
        return stats
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
