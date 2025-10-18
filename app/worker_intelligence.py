"""
Worker Intelligence - Traite les messages avec intelligence conversationnelle

- Pre-processing (typing, history, memory)
- Analyse contextuelle
- Timing adaptatif
- Génération réponse
- Update memory
"""

import asyncio
import json
import logging
from datetime import datetime
from supabase import create_client, Client, ClientOptions
import redis.asyncio as redis
from openai import OpenAI

from app.config import settings
from app.pre_processing import PreProcessor
from app.analysis import message_analyzer
from app.utils.timing import timing_engine

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkerIntelligence:
    """Worker intelligent avec analyse contextuelle complète"""
    
    def __init__(self):
        self.supabase: Client = None
        self.redis_client = None
        self.openai_client = None
        self.pre_processor = None
        
    async def connect_supabase(self):
        """Connexion Supabase"""
        logger.info("🔌 Connexion à Supabase...")
        
        options = ClientOptions(
            headers={
                "apikey": settings.supabase_service_key,
                "Authorization": f"Bearer {settings.supabase_service_key}"
            }
        )
        
        self.supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
            options=options
        )
        self.pre_processor = PreProcessor(self.supabase)
        logger.info("✅ Connecté à Supabase")
        
    async def connect_redis(self):
        """Connexion Redis"""
        logger.info("🔌 Connexion à Redis...")
        self.redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("✅ Connecté à Redis")
    
    def connect_openai(self):
        """Connexion OpenRouter"""
        logger.info("🔌 Connexion à OpenRouter...")
        self.openai_client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key
        )
        logger.info("✅ Connecté à OpenRouter")
    
    def build_prompt(
        self,
        bot_profile: dict,
        memory: dict,
        history: list,
        current_message: str,
        analysis: dict
    ) -> str:
        """Construit un prompt enrichi avec full context"""
        system_prompt = bot_profile.get('system_prompt', '')
        
        # Mémoire long-terme
        memory_context = f"""
MÉMOIRE DE CETTE PERSONNE:
- Nom: {memory.get('user_name', 'inconnu')}
- Niveau relation: {memory.get('relationship_level', 'stranger')}
- Trust score: {memory.get('trust_score', 0)}/100
- Ton conversation: {memory.get('conversation_tone', 'neutral')}
- Topics préférés: {', '.join(memory.get('preferred_topics', [])) or 'aucun'}
- Topics à éviter: {', '.join(memory.get('topics_to_avoid', [])) or 'aucun'}
"""
        
        # Historique (derniers 30 messages max pour prompt)
        history_context = "\n".join([
            f"{msg['sender_name']}: {msg['content']}"
            for msg in history[-30:]
        ])
        
        # Analysis
        analysis_context = f"""
ANALYSE DU MESSAGE:
- Urgence: {analysis['urgency']}/5
- Complexité: {analysis['complexity']}/5
- Ton émotionnel: {analysis['emotional_tone']}
- Type: {analysis['message_type']}
"""
        
        # Instructions adaptatives
        instructions = "INSTRUCTIONS:\n"
        
        if analysis['urgency'] >= 4:
            instructions += "- Réponds rapidement et directement\n"
        
        if analysis['requires_multi_messages']:
            instructions += "- Découpe ta réponse en 2-3 messages courts et naturels\n"
            instructions += "- Format: message1|||message2|||message3 (séparés par |||)\n"
        else:
            instructions += "- Un seul message naturel suffit\n"
        
        if memory.get('trust_score', 0) >= 70:
            instructions += "- Relation établie, sois plus authentique et intime\n"
        else:
            instructions += "- Relation naissante, reste naturel mais léger\n"
        
        # Assembler
        full_prompt = f"""{system_prompt}

{memory_context}

HISTORIQUE CONVERSATION:
{history_context}

{analysis_context}

{instructions}

MESSAGE ACTUEL:
{current_message}

TA RÉPONSE:"""
        
        return full_prompt
    
    def generate_response(self, prompt: str, temperature: float = 0.8) -> str:
        """Génère une réponse avec Grok"""
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.openrouter_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Erreur génération: {e}")
            return "Désolé, j'ai un petit bug technique 😅"
    
    async def activate_typing(self, bot_id: str, match_id: str):
        """Active l'indicateur de frappe"""
        try:
            self.supabase.table('typing_events').upsert({
                'user_id': bot_id,
                'match_id': match_id,
                'is_typing': True,
                'started_at': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"❌ Erreur activate typing: {e}")
    
    async def deactivate_typing(self, bot_id: str, match_id: str):
        """Désactive l'indicateur de frappe"""
        try:
            self.supabase.table('typing_events').upsert({
                'user_id': bot_id,
                'match_id': match_id,
                'is_typing': False,
                'updated_at': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            logger.error(f"❌ Erreur deactivate typing: {e}")
    
    async def send_message(self, match_id: str, bot_id: str, content: str):
        """Envoie un message"""
        try:
            self.supabase.table('messages').insert({
                'match_id': match_id,
                'sender_id': bot_id,
                'content': content,
                'type': 'text',
                'status': 'sent'
            }).execute()
            
            logger.info(f"✅ Message envoyé: {content[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi message: {e}")
            raise
    
    async def process_message(self, event_data: dict):
        """
        Traite un message avec intelligence complète
        """
        try:
            # Extraction données
            if event_data.get('type') == 'grouped':
                # Messages groupés
                messages = event_data['messages']
                match_id = event_data['match_id']
                bot_id = event_data['bot_id']
                # Prendre le dernier message comme principal
                main_msg = messages[-1]
                user_id = main_msg['sender_id']
                user_message = ' '.join([m['message_content'] for m in messages])
                logger.info(f"📦 Traitement {len(messages)} messages groupés")
            else:
                # Message simple
                match_id = event_data['match_id']
                bot_id = event_data['bot_id']
                user_id = event_data['sender_id']
                user_message = event_data['message_content']
            
            logger.info("=" * 60)
            logger.info(f"🤖 TRAITEMENT MESSAGE INTELLIGENT")
            logger.info(f"   Match: {match_id}")
            logger.info(f"   Message: {user_message[:100]}")
            logger.info("=" * 60)
            
            # =============================
            # PHASE 1: PRE-PROCESSING
            # =============================
            logger.info("\n📦 Phase 1: Pre-processing...")
            
            should_wait, context = await self.pre_processor.prepare_context(
                match_id, bot_id, user_id
            )
            
            if should_wait:
                # User tape encore, repousser le job
                logger.info("⏸️  User tape, on repousse le job...")
                await asyncio.sleep(2)
                await self.redis_client.rpush('bot_messages', json.dumps(event_data))
                return
            
            # =============================
            # PHASE 2: ANALYSE
            # =============================
            logger.info("\n🧠 Phase 2: Analyse contextuelle...")
            
            analysis = message_analyzer.analyze_message(
                user_message,
                context['history'],
                context['memory']
            )
            
            logger.info(f"   Urgency: {analysis['urgency']}/5")
            logger.info(f"   Complexity: {analysis['complexity']}/5")
            logger.info(f"   Tone: {analysis['emotional_tone']}")
            logger.info(f"   Multi-messages: {analysis['requires_multi_messages']}")
            
            # =============================
            # PHASE 3: TIMING - RÉFLEXION
            # =============================
            logger.info("\n⏱️  Phase 3: Calcul timing...")
            
            thinking_delay = timing_engine.calculate_thinking_delay(
                analysis,
                len(user_message),
                context['time_since_last_bot_minutes'] * 60  # Convertir en secondes
            )
            
            logger.info(f"   Délai réflexion: {thinking_delay}s")
            logger.info(f"⏳ Attente {thinking_delay}s (temps de réflexion)...")
            await asyncio.sleep(thinking_delay)
            
            # =============================
            # PHASE 4: ACTIVATION TYPING
            # =============================
            logger.info("\n⌨️  Phase 4: Activation typing...")
            await self.activate_typing(bot_id, match_id)
            
            # =============================
            # PHASE 5: GÉNÉRATION RÉPONSE
            # =============================
            logger.info("\n🧠 Phase 5: Génération réponse IA...")
            
            prompt = self.build_prompt(
                context['bot_profile'],
                context['memory'],
                context['history'],
                user_message,
                analysis
            )
            
            response = self.generate_response(
                prompt,
                context['bot_profile'].get('temperature', 0.8)
            )
            
            logger.info(f"✅ Réponse: {response[:100]}...")
            
            # Parser multi-messages si nécessaire
            if '|||' in response:
                messages_to_send = [m.strip() for m in response.split('|||')]
            else:
                messages_to_send = [response]
            
            # =============================
            # PHASE 6: ENVOI AVEC TIMING
            # =============================
            logger.info(f"\n📤 Phase 6: Envoi {len(messages_to_send)} message(s)...")
            
            for i, msg in enumerate(messages_to_send):
                # Calculer temps frappe
                typing_time = timing_engine.calculate_typing_time(msg)
                logger.info(f"   Message {i+1}: {typing_time}s de frappe")
                
                await asyncio.sleep(typing_time)
                
                # Envoyer
                await self.send_message(match_id, bot_id, msg)
                
                # Désactiver typing temporairement
                await self.deactivate_typing(bot_id, match_id)
                
                # Pause entre messages si plusieurs
                if i < len(messages_to_send) - 1:
                    pause = timing_engine.calculate_pause_between_messages(len(msg))
                    logger.info(f"   Pause: {pause}s")
                    await asyncio.sleep(pause)
                    
                    # Réactiver typing pour prochain
                    await self.activate_typing(bot_id, match_id)
            
            logger.info("\n✅ Message traité avec succès !")
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement: {e}", exc_info=True)
    
    async def run(self):
        """Lance le worker"""
        try:
            # Connexions
            await self.connect_supabase()
            await self.connect_redis()
            self.connect_openai()
            
            logger.info("=" * 60)
            logger.info("🧠 WORKER INTELLIGENCE ACTIF")
            logger.info("=" * 60)
            logger.info("👂 Écoute queue 'bot_messages'...")
            logger.info("⏳ En attente...")
            
            # Boucle de traitement
            while True:
                result = await self.redis_client.blpop('bot_messages', timeout=1)
                
                if result:
                    queue_name, message_json = result
                    event_data = json.loads(message_json)
                    
                    # Traiter
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
    """Point d'entrée"""
    worker = WorkerIntelligence()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
