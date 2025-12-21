#!/usr/bin/env python3
"""Test direct du traitement de l'email pour René QuiSait"""

import asyncio
import logging
import sys
from app.cron.check_emails import check_new_emails

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def test():
    print("Test du traitement de l'email pour René QuiSait")
    print("=" * 80)
    
    stats = await check_new_emails()
    
    print("\n" + "=" * 80)
    print("RÉSULTATS")
    print("=" * 80)
    print(f"Total emails: {stats.get('total_emails', 0)}")
    print(f"Courtiers identifiés: {stats.get('courtiers_identifies', 0)}")
    print(f"Erreurs: {stats.get('erreurs', 0)}")
    
    return stats.get('erreurs', 0) == 0

if __name__ == "__main__":
    asyncio.run(test())

