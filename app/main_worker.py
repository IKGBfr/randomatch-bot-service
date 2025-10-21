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

async def check_pending_initiations_loop(supabase_client, redis_client):
    """Boucle qui vérifie les initiations en attente toutes les 30s"""
    monitor = MatchMonitor(supabase_client, redis_client)
    logger.info("🔍 Initiation Checker démarré (toutes les 30s)")
    
    while True:
        try:
            await monitor.check_pending_initiations()
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Erreur check_pending_initiations: {e}")
            await asyncio.sleep(30)

async def check_abandoned_conversations_loop(supabase_client, redis_client):
    """Boucle qui détecte conversations abandonnées toutes les 60s"""
    monitor = MatchMonitor(supabase_client, redis_client)
    logger.info("🔄 Relance Checker démarré (toutes les 60s)")
    
    # Attendre 60s au démarrage pour laisser worker se stabiliser
    await asyncio.sleep(60)
    
    while True:
        try:
            await monitor.check_abandoned_conversations()
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Erreur check_abandoned_conversations: {e}")
            await asyncio.sleep(60)

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
    logger.info("🔄 Relance Checker : toutes les 60s (2-48h inactif)")
    logger.info("🕐 Timing Adaptatif : Phase 4 activé")
    logger.info("=" * 70)
    
    # Lancer les deux tâches en parallèle
    import json
    
    async def message_loop():
        """Boucle traitement messages"""
        try:
            logger.info("👂 Écoute queue 'bot_messages'...")
            
            # Vérifier que Redis est connecté
            if not worker.redis_client:
                logger.error("❌ Redis non connecté, impossible d'écouter la queue")
                return
            
            while True:
                try:
                    result = await worker.redis_client.blpop('bot_messages', timeout=1)
                    
                    if result:
                        queue_name, message_json = result
                        logger.info(f"📨 Message reçu de la queue: {message_json[:100]}...")
                        event_data = json.loads(message_json)
                        await worker.process_message(event_data)
                except Exception as e:
                    logger.error(f"Erreur traitement message: {e}", exc_info=True)
                    await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"❌ Erreur fatale message_loop: {e}", exc_info=True)
    
    try:
        # Lancer en parallèle
        await asyncio.gather(
            message_loop(),
            check_pending_initiations_loop(worker.supabase, worker.redis_client),
            check_abandoned_conversations_loop(worker.supabase, worker.redis_client)
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
