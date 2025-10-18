"""
Bridge utilisant polling SQL optimisé
Simple, fiable, fonctionne partout
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from supabase import create_client, Client
import redis.asyncio as redis
from app.config import settings

# Configuration du logger
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


class PollingBridge:
    """Bridge utilisant polling SQL optimisé"""
    
    def __init__(self):
        self.supabase: Client = None
        self.redis_client = None
        self.last_check = None
        self.processed_messages = set()  # Pour éviter les doublons
        
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
    
    async def check_new_messages(self):
        """Vérifie les nouveaux messages pour les bots"""
        try:
            # Chercher les messages des 10 dernières secondes non traités
            cutoff_time = datetime.utcnow() - timedelta(seconds=10)
            
            # Query SQL pour trouver les messages destinés aux bots
            response = self.supabase.rpc(
                'get_bot_messages',
                {
                    'since_timestamp': cutoff_time.isoformat()
                }
            ).execute()
            
            if response.data:
                for message in response.data:
                    message_id = message['message_id']
                    
                    # Éviter les doublons
                    if message_id in self.processed_messages:
                        continue
                    
                    # Marquer comme traité
                    self.processed_messages.add(message_id)
                    
                    # Pousser dans Redis
                    await self.push_to_redis(message)
                    
                # Nettoyer l'historique des messages traités (garder les 1000 derniers)
                if len(self.processed_messages) > 1000:
                    self.processed_messages = set(list(self.processed_messages)[-1000:])
                    
        except Exception as e:
            logger.error(f"❌ Erreur check messages: {e}")
    
    async def push_to_redis(self, event_data):
        """Pousse les données dans Redis"""
        try:
            await self.redis_client.rpush(
                'bot_messages',
                json.dumps(event_data)
            )
            logger.info(f"📨 Message poussé dans Redis queue")
            logger.info(f"   Bot: {event_data.get('bot_id')}")
            logger.info(f"   Match: {event_data.get('match_id')}")
        except Exception as e:
            logger.error(f"❌ Erreur push Redis: {e}")
    
    async def run(self):
        """Lancer le bridge"""
        try:
            # Connexions
            await self.connect_supabase()
            await self.connect_redis()
            
            logger.info("👂 Démarrage polling (intervalle: 5s)...")
            logger.info("⏳ En attente de messages...")
            
            # Boucle de polling
            while True:
                await self.check_new_messages()
                await asyncio.sleep(5)  # Check toutes les 5 secondes
                
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interruption utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
        finally:
            logger.info("🛑 Arrêt du bridge...")
            if self.redis_client:
                await self.redis_client.aclose()


async def main():
    """Point d'entrée principal"""
    logger.info("=" * 60)
    logger.info("🚀 RANDOMATCH BOT SERVICE - BRIDGE POLLING")
    logger.info("=" * 60)
    
    bridge = PollingBridge()
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())
