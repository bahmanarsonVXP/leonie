#!/usr/bin/env python3
"""
Script pour tester la classification Mistral sur tous les nouveaux emails
et afficher les détails de chaque classification.
"""

import asyncio
import logging
from app.cron.check_emails import check_new_emails

# Configuration du logging pour voir tous les détails
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    """Lance la vérification des emails avec logs détaillés."""
    print("=" * 80)
    print("TEST DE CLASSIFICATION MISTRAL - Tous les nouveaux emails")
    print("=" * 80)
    print()
    
    stats = await check_new_emails()
    
    print()
    print("=" * 80)
    print("RÉSUMÉ FINAL")
    print("=" * 80)
    print(f"Total emails récupérés: {stats['total_emails']}")
    print(f"Courtiers identifiés: {stats['courtiers_identifies']}")
    print(f"Clients identifiés: {stats['clients_identifies']}")
    print(f"Emails avec pièces jointes: {stats['emails_avec_pieces_jointes']}")
    print(f"Erreurs: {stats['erreurs']}")

if __name__ == "__main__":
    asyncio.run(main())

