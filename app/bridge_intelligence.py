"""
Bridge intelligent avec grouping des messages rapides
"""

import asyncio
import asyncpg
import json
import redis.asyncio as redis
from datetime import datetime
from typing import Dict
from app.config import settings
from app.redis_context import RedisContextManager
import logging

logger = logging.getLogger(__name__)


class BridgeIntelligence:
    """Bridge avec grouping intelligent"""
    
    def __init__(self):
        self.pg_conn = None
        self.redis_client = None
        self.context_manager = None
        self.running = False
        self.GROUPING_DELAY = 3  # Secondes
        
    async def connect_postgres(self):
        """Connexion PostgreSQL"""
        logger.info("🔌 Connexion à PostgreSQL...")
        self.pg_conn = await asyncpg.connect(
            settings.postgres_connection_string,
            server_settings={'jit': 'off'}
        )
        logger.info("✅ Connecté à PostgreSQL")
        
    async def connect_redis(self):
        """Connexion Redis"""
        logger.info("🔌 Connexion à Redis...")
        self.redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        self.context_manager = RedisContextManager(self.redis_client)
        logger.info("✅ Connecté à Redis")
    
    async def push_to_queue(self, message: Dict):
        """Pousse un message dans la queue"""
        queue_key = "bot_messages"
        await self.redis_client.rpush(queue_key, json.dumps(message))
        logger.info(f"✅ Message poussé dans queue")
    
    async def delayed_push(self, match_id: str):
        """
        Attendre X secondes puis pousser les messages groupés
        """
        await asyncio.sleep(self.GROUPING_DELAY)
        
        context = await self.context_manager.get_context(match_id)
        
        if context and len(context['messages']) > 0:
            # Créer payload groupé
            grouped = {
                'type': 'grouped',
                'count': context['rapid_count'],
                'messages': context['messages'],
                'match_id': match_id,
                'bot_id': context['messages'][0]['bot_id']
            }
            
            logger.info(f"📦 Grouping: {context['rapid_count']} messages")
            await self.push_to_queue(grouped)
            
            # Nettoyer contexte
            await self.context_manager.delete_context(match_id)
    
    async def handle_notification(self, connection, pid, channel, payload):
        """
        Callback PostgreSQL NOTIFY avec grouping intelligent
        """
        try:
            logger.info(f"📨 Notification reçue")
            
            message = json.loads(payload)
            match_id = message['match_id']
            
            # Récupérer contexte existant
            context = await self.context_manager.get_context(match_id)
            
            if context:
                # Contexte existe = messages rapides
                last_time = datetime.fromisoformat(context['last_message_at'])
                time_diff = (datetime.now() - last_time).total_seconds()
                
                if time_diff < self.GROUPING_DELAY:
                    # Ajouter au grouping
                    logger.info(f"🔄 Grouping: +1 message ({context['rapid_count'] + 1} total)")
                    await self.context_manager.update_context(match_id, message)
                    
                    # Démarrer timer si pas déjà fait
                    if not context.get('timer_started'):
                        context['timer_started'] = True
                        await self.context_manager.set_context(match_id, context)
                        asyncio.create_task(self.delayed_push(match_id))
                    
                    return  # Ne pas pousser maintenant
            
            # Nouveau contexte ou trop lent
            await self.context_manager.init_context(match_id, message)
            
            # Pousser immédiatement (premier message)
            await self.push_to_queue(message)
            
        except Exception as e:
            logger.error(f"❌ Erreur notification: {e}")
    
    async def start_listening(self):
        """Démarre l'écoute PostgreSQL"""
        logger.info("👂 Démarrage écoute 'bot_events'...")
        
        await self.pg_conn.add_listener('bot_events', self.handle_notification)
        
        logger.info("✅ Écoute active (avec grouping intelligent)")
        logger.info("⏳ En attente...")
        
        self.running = True
        
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.stop()
    
    async def stop(self):
        """Arrête le bridge"""
        logger.info("🛑 Arrêt bridge...")
        self.running = False
        
        if self.pg_conn:
            await self.pg_conn.remove_listener('bot_events', self.handle_notification)
            await self.pg_conn.close()
            
        if self.redis_client:
            await self.redis_client.close()
    
    async def run(self):
        """Lance le bridge"""
        logger.info("=" * 60)
        logger.info("🚀 BRIDGE INTELLIGENCE - GROUPING ACTIF")
        logger.info("=" * 60)
        
        try:
            await self.connect_postgres()
            await self.connect_redis()
            await self.start_listening()
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            await self.stop()
            raise


async def main():
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    
    bridge = BridgeIntelligence()
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())
