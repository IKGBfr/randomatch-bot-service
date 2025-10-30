"""
Processeur de messages schedulés pour traiter au réveil des bots.

Ce module :
- Vérifie périodiquement les messages en attente de traitement
- Traite les messages dont le scheduled_for est passé
- Respecte les horaires de disponibilité des bots
"""

import logging
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import Config
from app.supabase_client import SupabaseClient
from app.availability_checker import get_availability_checker
from app.worker_intelligence import WorkerIntelligence

logger = logging.getLogger(__name__)

# Timezone Europe/Paris
PARIS_TZ = ZoneInfo("Europe/Paris")


class ScheduledProcessor:
    """Traite les messages schedulés pour plus tard."""
    
    def __init__(self):
        self.supabase = SupabaseClient()
        self.worker = None
        self.availability_checker = None
        self.running = False
        
        # Configuration
        self.check_interval = 60  # Vérifier toutes les 60 secondes
        self.batch_size = 10  # Traiter max 10 messages par batch
    
    async def start(self):
        """Démarre le processeur de messages schedulés."""
        logger.info("🕐 Démarrage du ScheduledProcessor...")
        
        # Initialiser connexions
        await self.supabase.connect()
        self.availability_checker = await get_availability_checker()
        
        # Initialiser worker pour traiter les messages
        self.worker = WorkerIntelligence()
        await self.worker.connect()
        
        self.running = True
        logger.info("✅ ScheduledProcessor démarré")
        
        # Lancer le loop de vérification
        await self._process_loop()
    
    async def stop(self):
        """Arrête le processeur."""
        logger.info("🛑 Arrêt du ScheduledProcessor...")
        self.running = False
        
        if self.worker:
            await self.worker.close()
        
        await self.supabase.close()
        logger.info("✅ ScheduledProcessor arrêté")
    
    async def _process_loop(self):
        """Loop principal de vérification et traitement."""
        logger.info(f"🔄 Loop de vérification démarré (interval: {self.check_interval}s)")
        
        while self.running:
            try:
                await self._check_and_process_scheduled_messages()
                
                # Attendre avant la prochaine vérification
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Erreur dans process_loop: {e}", exc_info=True)
                # Continuer même en cas d'erreur
                await asyncio.sleep(self.check_interval)
    
    async def _check_and_process_scheduled_messages(self):
        """
        Vérifie et traite les messages schedulés dont l'heure est passée.
        """
        now = datetime.now(PARIS_TZ)
        
        # Requête pour trouver messages prêts à être traités
        query = """
            SELECT 
                id,
                message_id,
                match_id,
                bot_id,
                sender_id,
                scheduled_for,
                attempts
            FROM bot_message_queue
            WHERE status = 'pending'
              AND scheduled_for <= $1
              AND attempts < max_attempts
            ORDER BY scheduled_for ASC
            LIMIT $2
        """
        
        messages = await self.supabase.fetch(
            query,
            now,
            self.batch_size
        )
        
        if not messages:
            logger.debug("✅ Aucun message schedulé à traiter")
            return
        
        logger.info(f"📦 {len(messages)} message(s) schedulé(s) prêt(s) à traiter")
        
        # Traiter chaque message
        for msg in messages:
            await self._process_scheduled_message(msg)
    
    async def _process_scheduled_message(self, msg: dict):
        """
        Traite un message schedulé.
        
        Args:
            msg: dict avec id, message_id, match_id, bot_id, sender_id, etc.
        """
        bot_id = msg['bot_id']
        message_id = msg['message_id']
        match_id = msg['match_id']
        
        logger.info(
            f"🔄 Traitement message schedulé {message_id} "
            f"(bot: {bot_id}, match: {match_id})"
        )
        
        # Vérifier que le bot est maintenant disponible
        is_available, reason = await self.availability_checker.is_bot_available(bot_id)
        
        if not is_available:
            logger.info(
                f"⏰ Bot {bot_id} toujours indisponible: {reason}. "
                f"Re-scheduling message {message_id}..."
            )
            
            # Re-calculer prochaine disponibilité
            next_time = await self.availability_checker.get_next_available_time(bot_id)
            
            if next_time:
                # Mettre à jour le scheduled_for
                update_query = """
                    UPDATE bot_message_queue
                    SET scheduled_for = $1
                    WHERE id = $2
                """
                await self.supabase.execute(update_query, next_time, msg['id'])
                
                logger.info(
                    f"✅ Message {message_id} re-schedulé pour "
                    f"{next_time.strftime('%Y-%m-%d %H:%M')}"
                )
            
            return
        
        # Bot disponible, traiter le message
        logger.info(f"✅ Bot {bot_id} disponible, traitement du message {message_id}")
        
        try:
            # Charger le message complet depuis la DB
            message_query = """
                SELECT 
                    m.id,
                    m.match_id,
                    m.sender_id,
                    m.content,
                    m.created_at,
                    m.type
                FROM messages m
                WHERE m.id = $1
            """
            
            message = await self.supabase.fetch_one(message_query, message_id)
            
            if not message:
                logger.error(f"❌ Message {message_id} introuvable dans DB")
                # Supprimer de la queue
                await self._delete_from_queue(msg['id'])
                return
            
            # Créer payload pour le worker
            payload = {
                'type': 'scheduled',
                'message_id': message['id'],
                'match_id': message['match_id'],
                'bot_id': bot_id,
                'sender_id': message['sender_id'],
                'message_content': message['content'],  # worker attend 'message_content'
                'created_at': message['created_at'].isoformat() if hasattr(message['created_at'], 'isoformat') else str(message['created_at']),
                'was_scheduled': True  # Flag pour tracking
            }
            
            # Traiter avec le worker
            await self.worker.process_message(payload)
            
            logger.info(f"✅ Message schedulé {message_id} traité avec succès")
            
            # Supprimer de la queue
            await self._delete_from_queue(msg['id'])
            
        except Exception as e:
            logger.error(
                f"❌ Erreur traitement message schedulé {message_id}: {e}",
                exc_info=True
            )
            
            # Incrémenter attempts
            update_query = """
                UPDATE bot_message_queue
                SET 
                    attempts = attempts + 1,
                    last_error = $1
                WHERE id = $2
            """
            await self.supabase.execute(update_query, str(e), msg['id'])
            
            # Si max attempts atteints, marquer comme failed
            if msg['attempts'] + 1 >= 3:  # max_attempts = 3
                logger.error(
                    f"❌ Message {message_id} a échoué après {msg['attempts'] + 1} tentatives"
                )
                await self._mark_as_failed(msg['id'], str(e))
    
    async def _delete_from_queue(self, queue_id: str):
        """Supprime un message de la queue après traitement."""
        query = """
            DELETE FROM bot_message_queue
            WHERE id = $1
        """
        await self.supabase.execute(query, queue_id)
        logger.debug(f"🗑️ Message queue {queue_id} supprimé")
    
    async def _mark_as_failed(self, queue_id: str, error: str):
        """Marque un message comme échoué définitivement."""
        query = """
            UPDATE bot_message_queue
            SET 
                status = 'failed',
                last_error = $1,
                completed_at = NOW()
            WHERE id = $2
        """
        await self.supabase.execute(query, error, queue_id)
        logger.warning(f"⚠️ Message queue {queue_id} marqué comme failed")


# Instance globale
_scheduled_processor = None


async def get_scheduled_processor() -> ScheduledProcessor:
    """Retourne l'instance globale du processor (singleton)."""
    global _scheduled_processor
    
    if _scheduled_processor is None:
        _scheduled_processor = ScheduledProcessor()
    
    return _scheduled_processor


async def start_scheduled_processor():
    """Démarre le processeur de messages schedulés."""
    processor = await get_scheduled_processor()
    await processor.start()


if __name__ == "__main__":
    # Test standalone
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        processor = ScheduledProcessor()
        
        try:
            await processor.start()
        except KeyboardInterrupt:
            logger.info("Interruption clavier détectée")
        finally:
            await processor.stop()
    
    asyncio.run(main())
