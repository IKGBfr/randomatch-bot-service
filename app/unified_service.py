"""
Service unifié lançant Bridge + Worker en parallèle.
À utiliser comme entry point unique Railway.
"""
import asyncio
import logging

# Import des deux services
from app.bridge_intelligence import main as bridge_main
from app.main_worker import main as worker_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def unified_service():
    """Lance Bridge + Worker en parallèle avec asyncio.gather"""
    
    logger.info("="  * 70)
    logger.info("🚀 SERVICE UNIFIÉ - BRIDGE + WORKER")
    logger.info("=" * 70)
    
    try:
        # Lancer les deux services en parallèle
        await asyncio.gather(
            bridge_main(),  # Écoute PostgreSQL NOTIFY
            worker_main(),  # Traite messages Redis
        )
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interruption utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
    finally:
        logger.info("🛑 Arrêt du service unifié")


if __name__ == "__main__":
    asyncio.run(unified_service())
