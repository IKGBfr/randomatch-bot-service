"""
Worker qui traite les messages de la queue Redis
et génère les réponses des bots
"""

import asyncio
import json
import logging
from datetime import datetime
from supabase import create_client, Client
import redis.asyncio as redis
from openai import OpenAI
from app.config import settings

# Configuration du logger
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


class BotWorker:
    """Worker qui traite les messages de la queue"""
    
    def __init__(self):
        self.supabase: Client = None
        self.redis_client = None
        self.openai_client = None
        
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
    
    def connect_openai(self):
        """Connexion à OpenRouter (compatible OpenAI)"""
        logger.info("🔌 Connexion à OpenRouter...")
        self.openai_client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key
        )
        logger.info("✅ Connecté à OpenRouter")
    
    def generate_response(self, system_prompt: str, user_message: str) -> str:
        """Génère une réponse avec Grok"""
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.openrouter_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                temperature=0.8
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ Erreur génération réponse: {e}")
            # Fallback response
            return "Désolé, j'ai un petit souci technique 😅"
    
    async def send_message(self, match_id: str, bot_id: str, content: str):
        """Envoie un message dans Supabase"""
        try:
            result = self.supabase.table('messages').insert({
                'match_id': match_id,
                'sender_id': bot_id,
                'content': content,
                'type': 'text',
                'status': 'sent'
            }).execute()
            
            logger.info(f"✅ Message envoyé: {content[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi message: {e}")
            raise
    
    async def process_message(self, event_data: dict):
        """Traite un message de la queue"""
        try:
            match_id = event_data['match_id']
            bot_id = event_data['bot_id']
            user_message = event_data['message_content']
            
            logger.info("=" * 60)
            logger.info(f"🤖 Traitement message")
            logger.info(f"   Match: {match_id}")
            logger.info(f"   Bot: {bot_id}")
            logger.info(f"   Message: {user_message[:100]}")
            
            # Récupérer le system prompt du bot
            bot_profile = self.supabase.table('bot_profiles').select(
                'system_prompt'
            ).eq('id', bot_id).single().execute()
            
            if not bot_profile.data:
                logger.error(f"❌ Bot profile non trouvé: {bot_id}")
                return
            
            system_prompt = bot_profile.data['system_prompt']
            
            # Générer la réponse
            logger.info("🧠 Génération réponse IA...")
            response = self.generate_response(system_prompt, user_message)
            logger.info(f"✅ Réponse générée: {response[:100]}...")
            
            # Envoyer la réponse
            logger.info("📤 Envoi réponse...")
            await self.send_message(match_id, bot_id, response)
            
            logger.info("✅ Message traité avec succès !")
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}", exc_info=True)
    
    async def run(self):
        """Lancer le worker"""
        try:
            # Connexions
            await self.connect_supabase()
            await self.connect_redis()
            self.connect_openai()
            
            logger.info("👂 Démarrage worker (écoute queue 'bot_messages')...")
            logger.info("⏳ En attente de messages...")
            
            # Boucle de traitement
            while True:
                # BLPOP : attente bloquante sur la queue (timeout 1s)
                result = await self.redis_client.blpop('bot_messages', timeout=1)
                
                if result:
                    queue_name, message_json = result
                    event_data = json.loads(message_json)
                    
                    # Traiter le message
                    await self.process_message(event_data)
                    
        except KeyboardInterrupt:
            logger.info("\n⚠️  Interruption utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
        finally:
            logger.info("🛑 Arrêt du worker...")
            if self.redis_client:
                await self.redis_client.aclose()


async def main():
    """Point d'entrée principal"""
    logger.info("=" * 60)
    logger.info("🤖 RANDOMATCH BOT SERVICE - WORKER")
    logger.info("=" * 60)
    
    worker = BotWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
