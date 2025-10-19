"""
Worker principal orchestrant tous les systèmes bot.
Gère : messages, initiations post-match, timing adaptatif horaire.
"""
import asyncio
import logging
from datetime import datetime

from app.worker_intelligence import WorkerIntelligence
from app.match_monitor import MatchMonitor
from app.supabase_client import SupabaseClient
from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_pending_initiations_loop(supabase_client):
    """Boucle qui vérifie les initiations en attente toutes les 30s"""
    # Utiliser notre SupabaseClient custom (comme worker_intelligence)
    monitor = MatchMonitor(supabase_client)
    logger.info("🔍 Initiation Checker démarré (toutes les 30s)")
    
    while True:
        try:
            await monitor.check_pending_initiations()
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Erreur check_pending_initiations: {e}")
            await asyncio.sleep(30)

async def main():
    """Lance worker messages + checker initiations en parallèle"""
    
    # Worker principal
    worker = WorkerIntelligence()
    
    # Connexions
    await worker.connect_supabase()
    await worker.connect_redis()
    worker.connect_openai()
    
    logger.info("=" * 70)
    logger.info("🚀 MAIN WORKER - SYSTÈMES ACTIFS")
    logger.info("=" * 70)
    logger.info("📨 Worker Messages : bot_messages queue")
    logger.info("🔍 Initiation Checker : toutes les 30s")
    logger.info("🕐 Timing Adaptatif : Phase 4 activé")
    logger.info("=" * 70)
    
    # Lancer les deux tâches en parallèle
    import json
    
    async def message_loop():
        """Boucle traitement messages"""
        logger.info("👂 Écoute queue 'bot_messages'...")
        while True:
            result = await worker.redis_client.blpop('bot_messages', timeout=1)
            
            if result:
                queue_name, message_json = result
                event_data = json.loads(message_json)
                await worker.process_message(event_data)
    
    try:
        # Lancer en parallèle
        await asyncio.gather(
            message_loop(),
            check_pending_initiations_loop(worker.supabase)
        )
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interruption utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
    finally:
        logger.info("🛑 Arrêt du worker...")
        if worker.redis_client:
            await worker.redis_client.aclose()
        if worker.supabase:
            await worker.supabase.close()

if __name__ == "__main__":
    asyncio.run(main())
