"""
Test du bridge PostgreSQL NOTIFY
"""

import asyncio
from app.bridge import PostgreSQLBridge
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_bridge():
    """Test basique du bridge"""
    logger.info("=" * 60)
    logger.info("🧪 TEST DU BRIDGE POSTGRESQL NOTIFY")
    logger.info("=" * 60)
    
    bridge = PostgreSQLBridge()
    
    try:
        # Test connexions
        logger.info("\n1️⃣ Test connexion PostgreSQL...")
        await bridge.connect_postgres()
        
        logger.info("\n2️⃣ Test connexion Redis...")
        await bridge.connect_redis()
        
        logger.info("\n3️⃣ Test écoute NOTIFY...")
        logger.info("Le bridge va écouter pendant 30 secondes.")
        logger.info("Envoie un message dans Flutter pour tester !")
        
        # Écoute pendant 30 secondes
        await bridge.pg_conn.add_listener('bot_events', bridge.handle_notification)
        await asyncio.sleep(30)
        
        logger.info("\n✅ Test terminé !")
        
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
    finally:
        await bridge.stop()


if __name__ == "__main__":
    asyncio.run(test_bridge())
