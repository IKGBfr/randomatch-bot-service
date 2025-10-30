"""
Test des horaires de disponibilité des bots.

Ce script teste :
1. Vérification de disponibilité en temps réel
2. Calcul du délai jusqu'à la prochaine disponibilité
3. Gestion weekend/semaine
4. Timezone Europe/Paris
"""

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.availability_checker import get_availability_checker
from app.config import Config

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Timezone Paris
PARIS_TZ = ZoneInfo("Europe/Paris")


async def test_bot_availability(bot_id: str, bot_name: str):
    """Teste la disponibilité d'un bot spécifique."""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🤖 Test de disponibilité : {bot_name}")
    logger.info(f"{'='*60}")
    
    # Initialiser checker
    checker = await get_availability_checker()
    
    # Heure actuelle
    now = datetime.now(PARIS_TZ)
    is_weekend = now.weekday() in [5, 6]
    day_type = "🌴 Weekend" if is_weekend else "💼 Semaine"
    
    logger.info(f"📅 Date: {now.strftime('%Y-%m-%d %A')}")
    logger.info(f"🕐 Heure: {now.strftime('%H:%M:%S')} (Paris)")
    logger.info(f"📆 Type: {day_type}")
    
    # Vérifier disponibilité
    is_available, reason = await checker.is_bot_available(bot_id)
    
    if is_available:
        logger.info(f"✅ {bot_name} est DISPONIBLE")
        logger.info(f"   ➤ Peut répondre aux messages")
    else:
        logger.info(f"❌ {bot_name} est INDISPONIBLE")
        logger.info(f"   ➤ Raison: {reason}")
        
        # Calculer quand il sera disponible
        delay_seconds = await checker.calculate_delay_until_available(bot_id)
        
        if delay_seconds:
            hours = delay_seconds / 3600
            minutes = (delay_seconds % 3600) / 60
            
            next_available = now.timestamp() + delay_seconds
            next_datetime = datetime.fromtimestamp(next_available, tz=PARIS_TZ)
            
            logger.info(f"   ⏰ Sera disponible dans: {int(hours)}h {int(minutes)}min")
            logger.info(f"   📅 Prochain réveil: {next_datetime.strftime('%Y-%m-%d %H:%M')}")
    
    logger.info("")
    
    return is_available


async def test_all_bots():
    """Teste tous les bots configurés."""
    
    logger.info("\n" + "="*70)
    logger.info("🧪 TEST DES HORAIRES DE DISPONIBILITÉ DES BOTS")
    logger.info("="*70 + "\n")
    
    # Liste des bots à tester
    bots = [
        (Config.BOT_CAMILLE_ID, "Camille"),
        (Config.BOT_PAUL_ID, "Paul")
    ]
    
    results = {}
    
    for bot_id, bot_name in bots:
        if not bot_id:
            logger.warning(f"⚠️ Bot {bot_name} : ID non configuré (vérifier .env)")
            continue
        
        try:
            is_available = await test_bot_availability(bot_id, bot_name)
            results[bot_name] = is_available
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de {bot_name}: {e}")
            results[bot_name] = None
    
    # Résumé
    logger.info("="*70)
    logger.info("📊 RÉSUMÉ DES TESTS")
    logger.info("="*70)
    
    for bot_name, is_available in results.items():
        if is_available is None:
            status = "⚠️ ERREUR"
        elif is_available:
            status = "✅ DISPONIBLE"
        else:
            status = "❌ INDISPONIBLE"
        
        logger.info(f"  {bot_name:15} : {status}")
    
    logger.info("="*70 + "\n")


async def test_specific_times():
    """Teste des horaires spécifiques pour debug."""
    
    logger.info("\n" + "="*70)
    logger.info("🕐 TEST DES PLAGES HORAIRES")
    logger.info("="*70 + "\n")
    
    checker = await get_availability_checker()
    
    # Horaires configurés
    expected_schedules = {
        "Camille": {
            "weekday": "07:30 - 23:00",
            "weekend": "08:00 - 23:30"
        },
        "Paul": {
            "weekday": "07:30 - 23:00",
            "weekend": "08:00 - 23:30"
        }
    }
    
    logger.info("📋 Horaires configurés dans la DB:")
    for bot_name, schedule in expected_schedules.items():
        logger.info(f"\n  {bot_name}:")
        logger.info(f"    • Semaine : {schedule['weekday']}")
        logger.info(f"    • Weekend : {schedule['weekend']}")
    
    logger.info("\n" + "-"*70 + "\n")
    
    # Tester avec l'heure actuelle
    now = datetime.now(PARIS_TZ)
    logger.info(f"🕐 Test avec l'heure actuelle : {now.strftime('%H:%M')}")
    
    for bot_id, bot_name in [(Config.BOT_CAMILLE_ID, "Camille"), (Config.BOT_PAUL_ID, "Paul")]:
        if not bot_id:
            continue
        
        is_available, reason = await checker.is_bot_available(bot_id)
        
        status = "✅ Disponible" if is_available else "❌ Indisponible"
        logger.info(f"  {bot_name}: {status}")
        if reason:
            logger.info(f"    Raison: {reason}")
    
    logger.info("\n" + "="*70 + "\n")


async def main():
    """Point d'entrée principal."""
    try:
        # Test 1: Disponibilité actuelle de tous les bots
        await test_all_bots()
        
        # Test 2: Vérification des plages horaires
        await test_specific_times()
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests: {e}", exc_info=True)
    finally:
        # Cleanup
        checker = await get_availability_checker()
        await checker.close()


if __name__ == "__main__":
    asyncio.run(main())
