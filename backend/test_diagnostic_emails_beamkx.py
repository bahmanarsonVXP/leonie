#!/usr/bin/env python3
"""
Script de diagnostic pour les emails de BEAMKX@gamile.com non traités.

Ce script teste chaque étape du pipeline de traitement des emails:
1. Récupération IMAP
2. Identification du courtier
3. Classification Mistral
4. Routing vers les workflows
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List

from app.cron.check_emails import check_new_emails
from app.models.email import EmailData
from app.services.email_fetcher import EmailFetcher
from app.services.email_parser import EmailParser
from app.services.router import EmailRouter
from app.utils.db import get_courtier_by_email

# Configuration du logging pour voir les détails
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_emails_beamkx():
    """Test complet du pipeline pour les emails de BEAMKX@gamile.com"""
    
    print("=" * 80)
    print("DIAGNOSTIC EMAILS BEAMKX@gamile.com")
    print("=" * 80)
    
    # 1. Vérifier que le courtier existe dans la base
    print("\n" + "=" * 80)
    print("1. VÉRIFICATION DU COURTIER DANS LA BASE DE DONNÉES")
    print("=" * 80)
    
    email_courtier = "BEAMKX@gamile.com"
    courtier_db = get_courtier_by_email(email_courtier.lower())
    
    if not courtier_db:
        # Essayer avec différentes variantes
        variants = [
            email_courtier,
            email_courtier.lower(),
            email_courtier.upper(),
            "beamkx@gmail.com",  # En cas de typo dans l'email
        ]
        
        print(f"❌ Courtier non trouvé avec: {email_courtier}")
        print(f"   Tentative avec différentes variantes...")
        for variant in variants:
            courtier_db = get_courtier_by_email(variant)
            if courtier_db:
                print(f"   ✅ Trouvé avec: {variant}")
                email_courtier = variant
                break
    else:
        print(f"✅ Courtier trouvé dans la base:")
        print(f"   ID: {courtier_db.get('id')}")
        print(f"   Nom: {courtier_db.get('prenom')} {courtier_db.get('nom')}")
        print(f"   Email: {courtier_db.get('email')}")
        print(f"   Actif: {courtier_db.get('actif')}")
    
    if not courtier_db:
        print("\n❌ ERREUR: Courtier non trouvé dans la base de données")
        print("   Les emails ne peuvent pas être traités sans courtier identifié.")
        return
    
    # 2. Récupérer les emails depuis IMAP
    print("\n" + "=" * 80)
    print("2. RÉCUPÉRATION DES EMAILS DEPUIS IMAP")
    print("=" * 80)
    
    print("   Connexion IMAP et récupération des emails...")
    try:
        with EmailFetcher() as fetcher:
            # Récupérer les emails des 7 derniers jours pour être sûr de tout avoir
            # On va temporairement modifier la config pour forcer la récupération
            from app.utils.db import get_config, set_config
            
            # Sauvegarder le timestamp actuel
            old_config = get_config("last_email_check")
            
            # Forcer la récupération des 7 derniers jours
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            set_config(
                "last_email_check",
                {"timestamp": seven_days_ago.isoformat()},
                "Dernière vérification emails IMAP (pour test)"
            )
            
            try:
                emails = fetcher.fetch_new_emails()
            finally:
                # Restaurer l'ancien timestamp
                if old_config:
                    set_config(
                        "last_email_check",
                        old_config,
                        "Dernière vérification emails IMAP"
                    )
            
            print(f"   ✓ {len(emails)} email(s) récupéré(s) au total")
            
    except Exception as e:
        print(f"   ❌ Erreur lors de la récupération IMAP: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Filtrer les emails de BEAMKX@gamile.com
    print("\n" + "=" * 80)
    print("3. FILTRAGE DES EMAILS DE BEAMKX@gamile.com")
    print("=" * 80)
    
    emails_beamkx = []
    variants_to_check = [
        "BEAMKX@gamile.com",
        "beamkx@gamile.com",
        "BEAMKX@GAMILE.COM",
        "beamkx@gmail.com",  # En cas de typo
    ]
    
    for email in emails:
        email_from = email.from_address.lower()
        if any(variant.lower() == email_from for variant in variants_to_check):
            emails_beamkx.append(email)
    
    if not emails_beamkx:
        print(f"   ❌ Aucun email trouvé de BEAMKX@gamile.com")
        print(f"\n   Emails récupérés (expéditeurs uniques):")
        unique_senders = {}
        for email in emails:
            sender = email.from_address.lower()
            if sender not in unique_senders:
                unique_senders[sender] = email
                print(f"     - {email.from_address}: {email.subject[:60]}")
        return
    
    print(f"   ✅ {len(emails_beamkx)} email(s) trouvé(s) de BEAMKX@gamile.com")
    
    # Trier par date (plus récents en premier)
    emails_beamkx.sort(key=lambda e: e.date, reverse=True)
    
    for idx, email in enumerate(emails_beamkx, 1):
        print(f"\n   Email {idx}:")
        print(f"     Sujet: {email.subject}")
        print(f"     Date: {email.date}")
        print(f"     From: {email.from_address}")
        print(f"     Message-ID: {email.message_id}")
    
    # 4. Test de l'identification du courtier pour chaque email
    print("\n" + "=" * 80)
    print("4. TEST IDENTIFICATION COURTIER")
    print("=" * 80)
    
    for idx, email in enumerate(emails_beamkx, 1):
        print(f"\n   Email {idx}: {email.subject[:50]}")
        courtier = EmailParser.identify_courtier(email)
        
        if courtier:
            print(f"     ✅ Courtier identifié: {courtier.get('prenom')} {courtier.get('nom')}")
            print(f"        Email DB: {courtier.get('email')}")
            print(f"        Email email: {email.from_address}")
            print(f"        Actif: {courtier.get('actif')}")
        else:
            print(f"     ❌ Courtier NON identifié")
            print(f"        Email recherché: {email.from_address}")
            print(f"        Problème: Le courtier n'a pas pu être identifié")
    
    # 5. Test du traitement complet (comme dans check_new_emails)
    print("\n" + "=" * 80)
    print("5. TEST TRAITEMENT COMPLET (IDENTIFICATION + CLASSIFICATION + ROUTING)")
    print("=" * 80)
    
    for idx, email in enumerate(emails_beamkx[:2], 1):  # Tester les 2 premiers
        print(f"\n{'='*80}")
        print(f"TRAITEMENT EMAIL {idx}/{min(2, len(emails_beamkx))}: {email.subject[:60]}")
        print(f"{'='*80}")
        
        try:
            # Identification courtier
            courtier = EmailParser.identify_courtier(email)
            if not courtier:
                print(f"❌ Courtier non identifié - arrêt du traitement")
                continue
            
            print(f"✅ Courtier identifié: {courtier.get('prenom')} {courtier.get('nom')}")
            
            # Identification client
            client = EmailParser.identify_client(email, courtier.get("id"))
            if client:
                print(f"✅ Client identifié: {client.get('prenom')} {client.get('nom')}")
            else:
                print(f"ℹ️  Client non identifié (nouveau dossier probable)")
            
            # Classification Mistral
            print(f"\n📊 Classification Mistral en cours...")
            classification = await EmailParser.classify_with_mistral(email, courtier, client)
            
            print(f"✅ Classification réussie:")
            print(f"   Action: {classification.action.value}")
            print(f"   Confiance: {classification.confiance:.2%}")
            print(f"   Résumé: {classification.resume}")
            print(f"   Détails: {classification.details}")
            
            # Routing
            print(f"\n🔄 Routing vers workflow...")
            result = await EmailRouter.route(email, classification, courtier)
            
            print(f"✅ Résultat du routing:")
            print(f"   Status: {result.get('status')}")
            print(f"   Action: {result.get('action')}")
            print(f"   Message: {result.get('message')}")
            if 'job_id' in result:
                print(f"   Job ID: {result.get('job_id')}")
            
        except Exception as e:
            print(f"\n❌ ERREUR lors du traitement:")
            import traceback
            traceback.print_exc()
    
    # 6. Test avec la fonction check_new_emails complète
    print("\n" + "=" * 80)
    print("6. TEST AVEC check_new_emails() COMPLÈTE")
    print("=" * 80)
    print("   (Note: Cette fonction met à jour le timestamp, donc les emails")
    print("    déjà traités ne seront plus récupérés lors des prochains checks)")
    
    try:
        stats = await check_new_emails()
        print(f"\n📊 Statistiques:")
        print(f"   Total emails: {stats.get('total_emails')}")
        print(f"   Courtiers identifiés: {stats.get('courtiers_identifies')}")
        print(f"   Clients identifiés: {stats.get('clients_identifies')}")
        print(f"   Emails avec pièces jointes: {stats.get('emails_avec_pieces_jointes')}")
        print(f"   Erreurs: {stats.get('erreurs')}")
    except Exception as e:
        print(f"\n❌ Erreur lors de check_new_emails(): {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("FIN DU DIAGNOSTIC")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_emails_beamkx())

