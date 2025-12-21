#!/usr/bin/env python3
"""
Script rapide pour tester le traitement du nouvel email de BEAMKX@gmail.com
"""

import asyncio
import logging
from app.cron.check_emails import check_new_emails

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def test_nouvel_email():
    """Teste le traitement du nouvel email"""
    print("=" * 80)
    print("TEST TRAITEMENT NOUVEL EMAIL BEAMKX@gmail.com")
    print("=" * 80)
    print()
    
    try:
        stats = await check_new_emails()
        
        print("\n" + "=" * 80)
        print("RÉSULTATS")
        print("=" * 80)
        print(f"Total emails récupérés: {stats.get('total_emails', 0)}")
        print(f"Courtiers identifiés: {stats.get('courtiers_identifies', 0)}")
        print(f"Clients identifiés: {stats.get('clients_identifies', 0)}")
        print(f"Emails avec pièces jointes: {stats.get('emails_avec_pieces_jointes', 0)}")
        print(f"Erreurs: {stats.get('erreurs', 0)}")
        
        if stats.get('erreurs', 0) == 0:
            print("\n✅ Traitement réussi! Aucune erreur.")
        else:
            print(f"\n⚠️  {stats.get('erreurs', 0)} erreur(s) détectée(s)")
            
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_nouvel_email())

