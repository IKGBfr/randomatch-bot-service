"""
Scheduled Tasks - Tâches planifiées pour l'exit automatique

Unmatch automatique après 30min quand le bot a exit
"""
import asyncio
import logging
from datetime import datetime, timedelta
from app.supabase_client import SupabaseClient
from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def process_bot_exits():
    """
    Unmatch les conversations où le bot est parti depuis > 30 minutes
    À lancer toutes les 5-10 minutes via cron
    """
    supabase = SupabaseClient()
    await supabase.connect()
    
    try:
        logger.info("🔍 Recherche conversations à unmatch...")
        
        # Trouver matches où bot exit depuis > 30 min et pas encore unmatch
        cutoff_time = datetime.now() - timedelta(minutes=30)
        
        exits = await supabase.fetch(
            """
            SELECT m.id, m.user1_id, m.user2_id, m.bot_exit_reason, m.bot_exited_at,
                   CASE 
                       WHEN p1.is_bot THEN p1.id 
                       ELSE p2.id 
                   END as bot_id
            FROM matches m
            LEFT JOIN profiles p1 ON m.user1_id = p1.id
            LEFT JOIN profiles p2 ON m.user2_id = p2.id
            WHERE m.bot_exited_at IS NOT NULL
            AND m.bot_exited_at < $1
            AND NOT EXISTS (
                SELECT 1 FROM unmatched_pairs up
                WHERE (up.user1_id = m.user1_id AND up.user2_id = m.user2_id)
                   OR (up.user1_id = m.user2_id AND up.user2_id = m.user1_id)
            )
            """,
            cutoff_time
        )
        
        if not exits:
            logger.info("   ✅ Aucun match à unmatch")
            return
        
        logger.info(f"   📋 {len(exits)} match(s) à unmatch")
        
        for match in exits:
            try:
                match_id = match['id']
                user1_id = match['user1_id']
                user2_id = match['user2_id']
                bot_id = match['bot_id']
                reason = match['bot_exit_reason']
                exited_at = match['bot_exited_at']
                
                logger.info(f"   🔄 Unmatch {match_id[:8]}... (raison: {reason})")
                
                # Créer unmatch
                await supabase.execute(
                    """
                    INSERT INTO unmatched_pairs (user1_id, user2_id, unmatched_by)
                    VALUES ($1, $2, $3)
                    ON CONFLICT DO NOTHING
                    """,
                    user1_id,
                    user2_id,
                    bot_id
                )
                
                logger.info(f"      ✅ Unmatch créé")
                
            except Exception as e:
                logger.error(f"      ❌ Erreur unmatch {match_id}: {e}")
                continue
        
        logger.info(f"✅ Traitement terminé: {len(exits)} unmatch(s)")
        
    except Exception as e:
        logger.error(f"❌ Erreur process_bot_exits: {e}", exc_info=True)
    finally:
        await supabase.close()


async def main():
    """Point d'entrée"""
    logger.info("=" * 60)
    logger.info("🕒 SCHEDULED TASK - BOT EXITS")
    logger.info("=" * 60)
    
    await process_bot_exits()
    
    logger.info("=" * 60)
    logger.info("✅ Task terminée")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
