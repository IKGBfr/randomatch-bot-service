"""
Bridge alternatif utilisant Supabase Realtime au lieu de PostgreSQL NOTIFY
Compatible avec tous les environnements réseau
"""

import asyncio
import json
import logging
from supabase import create_client, Client
import redis.asyncio as redis
from app.config import settings

# Configuration du logger
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


class RealtimeBridge:
    """Bridge utilisant Supabase Realtime"""
    
    def __init__(self):
        self.supabase: Client = None
        self.redis_client = None
        self.channel = None
        
    async def connect_supabase(self):
        """Connexion à Supabase"""
        logger.info("🔌 Connexion à Supabase...")
        self.supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        logger.info("✅ Connecté à Supabase")
        
    async def connect_redis(self):
        """Connexion à Redis"""
        logger.info("🔌 Connexion à Redis...")
        self.redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("✅ Connecté à Redis")
    
    def handle_realtime_message(self, payload):
        """Gestionnaire de messages Realtime"""
        try:
            # Payload Supabase Realtime contient: record, old_record, eventType, etc.
            logger.info(f"📨 Message Realtime reçu: {payload.get('eventType')}")
            
            if payload.get('eventType') == 'INSERT':
                record = payload.get('new', {})
                message_id = record.get('id')
                sender_id = record.get('sender_id')
                match_id = record.get('match_id')
                content = record.get('content')
                
                # Vérifier si le message est pour un bot
                # On va regarder si le match contient un bot
                match_data = self.supabase.table('matches').select(
                    'user1_id, user2_id'
                ).eq('id', match_id).single().execute()
                
                if match_data.data:
                    user1_id = match_data.data.get('user1_id')
                    user2_id = match_data.data.get('user2_id')
                    
                    # Déterminer qui est le bot
                    bot_id = user2_id if sender_id == user1_id else user1_id
                    
                    # Vérifier si c'est un bot
                    bot_check = self.supabase.table('profiles').select(
                        'is_bot'
                    ).eq('id', bot_id).single().execute()
                    
                    if bot_check.data and bot_check.data.get('is_bot'):
                        # Construire le payload pour Redis
                        event_data = {
                            'match_id': match_id,
                            'bot_id': bot_id,
                            'user_id': sender_id,
                            'message_id': message_id,
                            'message_content': content,
                            'sender_id': sender_id,
                            'created_at': record.get('created_at')
                        }
                        
                        # Pousser dans Redis (synchrone dans le callback)
                        asyncio.create_task(
                            self.push_to_redis(event_data)
                        )
                        
        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")
    
    async def push_to_redis(self, event_data):
        """Pousse les données dans Redis"""
        try:
            await self.redis_client.rpush(
                'bot_messages',
                json.dumps(event_data)
            )
            logger.info(f"✅ Message poussé dans Redis queue 'bot_messages'")
            logger.info(f"   Bot: {event_data['bot_id']}")
            logger.info(f"   Match: {event_data['match_id']}")
        except Exception as e:
            logger.error(f"❌ Erreur push Redis: {e}")
    
    async def run(self):
        """Lancer le bridge"""
        try:
            # Connexions
            await self.connect_supabase()
            await self.connect_redis()
            
            # S'abonner à la table messages via Realtime
            logger.info("👂 Abonnement Realtime à la table 'messages'...")
            
            # Subscribe utilise l'API Python Supabase Realtime
            self.channel = self.supabase.channel('messages_channel')
            
            self.channel.on_postgres_changes(
                event='INSERT',
                schema='public',
                table='messages',
                callback=self.handle_realtime_message
            ).subscribe()
            
            logger.info("✅ Abonné à Realtime 'messages'")
            logger.info("⏳ En attente de messages...")
            
            # Garder le bridge actif
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interruption utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
        finally:
            logger.info("🛑 Arrêt du bridge...")
            if self.channel:
                self.supabase.remove_channel(self.channel)
            if self.redis_client:
                await self.redis_client.close()


async def main():
    """Point d'entrée principal"""
    logger.info("=" * 60)
    logger.info("🚀 RANDOMATCH BOT SERVICE - BRIDGE REALTIME")
    logger.info("=" * 60)
    
    bridge = RealtimeBridge()
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())
