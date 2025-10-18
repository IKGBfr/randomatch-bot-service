"""
Bridge PostgreSQL NOTIFY → Redis Queue

Écoute le canal PostgreSQL 'bot_events' 24/7 et pousse 
les messages dans Redis pour traitement par les workers.
"""

import asyncio
import asyncpg
import json
import redis.asyncio as redis
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgreSQLBridge:
    """Bridge entre PostgreSQL NOTIFY et Redis Queue"""
    
    def __init__(self):
        self.pg_conn = None
        self.redis_client = None
        self.running = False
        
    async def connect_postgres(self):
        """Connexion à PostgreSQL"""
        logger.info("🔌 Connexion à PostgreSQL...")
        # Forcer IPv4 pour éviter les problèmes de connexion IPv6
        import socket
        self.pg_conn = await asyncpg.connect(
            settings.postgres_connection_string,
            server_settings={'jit': 'off'},
        )
        logger.info("✅ Connecté à PostgreSQL")
        
    async def connect_redis(self):
        """Connexion à Redis"""
        logger.info("🔌 Connexion à Redis...")
        self.redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("✅ Connecté à Redis")
        
    async def handle_notification(self, connection, pid, channel, payload):
        """
        Callback appelé quand une notification PostgreSQL arrive
        
        Payload attendu (JSON):
        {
            "match_id": "uuid",
            "bot_id": "uuid", 
            "user_id": "uuid",
            "message_id": "uuid",
            "message_content": "text",
            "sender_id": "uuid"
        }
        """
        try:
            logger.info(f"📨 Notification reçue sur canal '{channel}'")
            
            # Parser le payload JSON
            data = json.loads(payload)
            logger.info(f"📦 Payload: {data}")
            
            # Pousser dans Redis queue
            queue_key = "bot_messages"
            await self.redis_client.rpush(queue_key, json.dumps(data))
            
            logger.info(f"✅ Message poussé dans Redis queue '{queue_key}'")
            logger.info(f"   Bot: {data.get('bot_id')}")
            logger.info(f"   Match: {data.get('match_id')}")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur parsing JSON: {e}")
        except Exception as e:
            logger.error(f"❌ Erreur traitement notification: {e}")
            
    async def start_listening(self):
        """Démarre l'écoute du canal PostgreSQL"""
        logger.info("👂 Démarrage écoute canal 'bot_events'...")
        
        # S'abonner au canal
        await self.pg_conn.add_listener('bot_events', self.handle_notification)
        
        logger.info("✅ Écoute active sur 'bot_events'")
        logger.info("⏳ En attente de notifications...")
        
        self.running = True
        
        # Boucle infinie pour garder le bridge actif
        try:
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n⚠️  Arrêt demandé (Ctrl+C)")
            await self.stop()
            
    async def stop(self):
        """Arrête le bridge proprement"""
        logger.info("🛑 Arrêt du bridge...")
        self.running = False
        
        if self.pg_conn:
            await self.pg_conn.remove_listener('bot_events', self.handle_notification)
            await self.pg_conn.close()
            logger.info("✅ Connexion PostgreSQL fermée")
            
        if self.redis_client:
            await self.redis_client.close()
            logger.info("✅ Connexion Redis fermée")
            
    async def run(self):
        """Lance le bridge complet"""
        logger.info("=" * 60)
        logger.info("🚀 RANDOMATCH BOT SERVICE - BRIDGE POSTGRESQL")
        logger.info("=" * 60)
        
        try:
            # Connexions
            await self.connect_postgres()
            await self.connect_redis()
            
            # Démarre l'écoute
            await self.start_listening()
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            await self.stop()
            raise


async def main():
    """Point d'entrée du bridge"""
    bridge = PostgreSQLBridge()
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())
