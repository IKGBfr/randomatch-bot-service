"""
Worker Intelligence - Traite les messages avec intelligence conversationnelle

✅ VERSION 3.0 - Anti-Double Réponse Robuste
- Lock Redis distribué (multi-instance safe)
- Monitoring continu (réflexion + frappe)
- Annulation si nouveaux messages détectés
"""

import asyncio
import json
import logging
from datetime import datetime
from app.supabase_client import SupabaseClient
import redis.asyncio as redis
from openai import OpenAI

from app.config import settings
from app.pre_processing import PreProcessor
from app.analysis import message_analyzer
from app.utils.timing import timing_engine
from app.exit_manager import ExitManager
from app.prompt_builder import prompt_builder
from app.response_cache import ResponseCache

# 🆕 NOUVEAUX IMPORTS
from app.conversation_lock import ConversationLock
from app.continuous_monitor import ContinuousMonitor
from app.unanswered_detector import UnansweredDetector  # 🆕 NOUVEAU

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WorkerIntelligence:
    """Worker intelligent avec lock distribué + monitoring continu"""
    
    def __init__(self):
        self.supabase: SupabaseClient = None
        self.redis_client = None
        self.openai_client = None
        self.pre_processor = None
        self.exit_manager = ExitManager(
            min_messages=15,
            max_messages=30,
            exit_chance=0.05
        )
        
        # 🆕 LOCK REDIS DISTRIBUÉ (remplace asyncio.Lock)
        self.conversation_lock: ConversationLock = None
        
        # 🆕 MONITORING CONTINU (remplace MessageMonitor)
        self.continuous_monitor: ContinuousMonitor = None
        
        # Response cache (conservé)
        self.response_cache: ResponseCache = None
        
        # 🆕 DÉTECTEUR MESSAGES SANS RÉPONSE
        self.unanswered_detector: UnansweredDetector = None
        
    async def connect_supabase(self):
        """Connexion Supabase custom client"""
        logger.info("🔌 Connexion à Supabase...")
        self.supabase = SupabaseClient()
        await self.supabase.connect()
        self.pre_processor = PreProcessor(self.supabase)
        
        # 🆕 Initialiser continuous monitor
        self.continuous_monitor = ContinuousMonitor(self.supabase)
        
        # 🆕 Initialiser unanswered detector
        self.unanswered_detector = UnansweredDetector()
        
        logger.info("✅ Connecté à Supabase + Continuous Monitor + Unanswered Detector")
        
    async def connect_redis(self):
        """Connexion Redis"""
        logger.info("🔌 Connexion à Redis...")
        self.redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        # 🆕 Initialiser conversation lock (Redis distribué)
        self.conversation_lock = ConversationLock(self.redis_client)
        
        # Response cache
        self.response_cache = ResponseCache(self.redis_client)
        
        logger.info("✅ Connecté à Redis + Lock distribué + Cache")
    
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
            f"{msg.get('profiles', {}).get('first_name', 'Inconnu')}: {msg['content']}"
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
            instructions += "- Sépare chaque message par ||| OU [MSG_BREAK] OU double saut de ligne\n"
            instructions += "- Exemple: 'Salut !|||Comment ça va ?|||Moi ça va bien'\n"
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
            await self.supabase.upsert('typing_events', {
                'user_id': bot_id,
                'match_id': match_id,
                'is_typing': True,
                'started_at': datetime.now()
            })
        except Exception as e:
            logger.error(f"❌ Erreur activate typing: {e}")
    
    async def deactivate_typing(self, bot_id: str, match_id: str):
        """Désactive l'indicateur de frappe"""
        try:
            await self.supabase.upsert('typing_events', {
                'user_id': bot_id,
                'match_id': match_id,
                'is_typing': False,
                'updated_at': datetime.now()
            })
        except Exception as e:
            logger.error(f"❌ Erreur deactivate typing: {e}")
    
    async def send_message(self, match_id: str, bot_id: str, content: str):
        """
        Envoie un message (avec interception [UNMATCH])
        
        Si le message contient [UNMATCH], le marqueur est retiré,
        l'unmatch est déclenché, et seul le message propre est envoyé.
        """
        try:
            # 🆕 INTERCEPTION [UNMATCH]
            from app.unmatch_handler import unmatch_handler
            
            clean_content, unmatch_triggered = await unmatch_handler.process_message_with_unmatch(
                content,
                match_id,
                bot_id
            )
            
            # Envoyer le message propre (sans [UNMATCH])
            await self.supabase.insert('messages', {
                'match_id': match_id,
                'sender_id': bot_id,
                'content': clean_content,
                'type': 'text',
                'status': 'sent'
            })
            
            if unmatch_triggered:
                logger.info(f"✅ Message envoyé + Unmatch déclenché: {clean_content[:50]}...")
            else:
                logger.info(f"✅ Message envoyé: {clean_content[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi message: {e}")
            raise
    
    async def process_message(self, event_data: dict):
        """
        ✅ VERSION 3.0 - Point d'entrée avec lock Redis distribué
        
        Garantit qu'un seul worker traite un match à la fois,
        même avec plusieurs instances Railway.
        """
        # Extraction match_id
        if event_data.get('type') == 'grouped':
            match_id = event_data['match_id']
        else:
            match_id = event_data['match_id']
        
        # ============================================
        # 🆕 TENTATIVE D'ACQUISITION DU LOCK REDIS
        # ============================================
        
        logger.info(f"🔒 Tentative acquisition lock Redis pour {match_id[:8]}...")
        
        lock_acquired = await self.conversation_lock.acquire(match_id, timeout=5)
        
        if not lock_acquired:
            logger.warning(
                f"⏸️  Match {match_id[:8]} déjà en traitement par un autre worker"
            )
            logger.warning("   → Message repoussé dans queue (attente 5s)")
            
            # Attendre et repousser
            await asyncio.sleep(5)
            await self.redis_client.rpush('bot_messages', json.dumps(event_data))
            return  # STOP - un autre worker s'en occupe
        
        logger.info(f"✅ Lock Redis acquis pour {match_id[:8]}")
        
        # ============================================
        # TRAITEMENT AVEC LOCK (toujours libéré)
        # ============================================
        
        try:
            await self._process_message_impl(event_data)
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement: {e}", exc_info=True)
            
            # Cleanup cache en cas d'erreur
            try:
                if self.response_cache:
                    await self.response_cache.clear_generating(match_id)
                    logger.info("🧹 Cache génération cleared (erreur)")
            except Exception as cache_err:
                logger.error(f"❌ Erreur clear cache: {cache_err}")
                
        finally:
            # ============================================
            # 🔒 TOUJOURS LIBÉRER LE LOCK REDIS
            # ============================================
            
            # 🔧 SAFETY: Clear cache génération (au cas où)
            try:
                if hasattr(self, 'response_cache') and self.response_cache:
                    # Vérifier si toujours en génération
                    is_gen = await self.response_cache.is_generating(match_id)
                    if is_gen:
                        await self.response_cache.clear_generating(match_id)
                        logger.warning("⚠️ Cache génération still set, cleared (finally)")
            except Exception as safety_err:
                logger.error(f"❌ Safety clear cache failed: {safety_err}")
            
            await self.conversation_lock.release(match_id)
            logger.info(f"🔓 Lock Redis libéré pour {match_id[:8]}")
    
    async def _process_message_impl(self, event_data: dict):
        """
        ✅ VERSION 3.0 - Implémentation avec monitoring continu
        
        Surveille les nouveaux messages pendant TOUTE la durée:
        - Réflexion (thinking delay)
        - Frappe (typing simulation)
        
        Annule et repousse si nouveaux messages détectés.
        """
        # Extraction données
        if event_data.get('type') == 'grouped':
            messages = event_data['messages']
            match_id = event_data['match_id']
            bot_id = event_data['bot_id']
            main_msg = messages[-1]
            user_id = main_msg['sender_id']
            user_message = ' '.join([m['message_content'] for m in messages])
            logger.info(f"📦 Traitement {len(messages)} messages groupés")
        else:
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
        # PHASE 0: DÉTECTION URGENCE (NOUVEAU)
        # =============================
        logger.info("\n🚨 Phase 0: Détection messages sans réponse...")
        
        # Charger historique préliminaire pour analyse urgence
        prelim_history = await self.pre_processor.fetch_conversation_history(match_id)
        
        # Analyser si réponse urgente nécessaire
        urgency_check = await self.unanswered_detector.needs_urgent_response(
            prelim_history
            # 🔧 bot_id n'est plus nécessaire (détection via is_bot)
        )
        
        force_response = False
        
        if urgency_check['urgent']:
            logger.warning("⚠️ RÉPONSE URGENTE NÉCESSAIRE!")
            logger.warning(f"   {urgency_check['consecutive_user_messages']} messages user consécutifs")
            logger.warning(f"   Context: {urgency_check['context']}")
            logger.warning(f"   Attente: {urgency_check['minutes_waiting']:.1f} minutes")
            
            force_response = True
            logger.info("🚨 Force response activé → Ignore cache")
        
        # =============================
        # PHASE 0bis: CHECK CACHE (génération en cours)
        # =============================
        
        if not force_response:
            logger.info("\n💾 Phase 0bis: Vérification cache...")
            
            if await self.response_cache.is_generating(match_id):
                logger.warning("⚠️ Génération déjà en cours (cache)")
                logger.warning("   → SKIP")
                return
            
            logger.info("✅ Pas de génération en cours")
        else:
            logger.info("⚠️ Cache ignoré (force_response)")
        
        # Marquer génération en cours
        await self.response_cache.mark_generating(match_id, user_message)
        
        # =============================
        # PHASE 1: PRE-PROCESSING
        # =============================
        logger.info("\n📦 Phase 1: Pre-processing...")
        
        context = await self.pre_processor.prepare_context(
            match_id, bot_id, user_id
        )
        
        if context['is_typing']:
            logger.info("⚠️ User tape encore → ABANDON")
            
            # 🔧 Clear cache avant de repousser
            await self.response_cache.clear_generating(match_id)
            logger.info("🧹 Cache génération cleared (user typing)")
            
            await asyncio.sleep(5)
            event_data['retry_count'] = event_data.get('retry_count', 0) + 1
            
            if event_data['retry_count'] <= 5:
                await self.redis_client.rpush('bot_messages', json.dumps(event_data))
                logger.info(f"📨 Repoussé (retry {event_data['retry_count']}/5)")
            else:
                logger.warning("❌ Trop de retry, abandon")
            
            return
        
        # =============================
        # PHASE 1.5: VÉRIFICATION LIMITE/EXIT (NOUVEAU)
        # =============================
        logger.info("\n🚨 Phase 1.5: Vérification limite bot...")
        
        match_info = await self.supabase.fetch_one(
            """
            SELECT bot_messages_count, bot_messages_limit, bot_exit_reason
            FROM matches
            WHERE id = $1
            """,
            match_id
        )
        
        if not match_info:
            logger.error(f"❌ Match {match_id} non trouvé")
            await self.response_cache.clear_generating(match_id)
            return
        
        count = match_info['bot_messages_count'] or 0
        limit = match_info['bot_messages_limit'] or 25
        exit_reason = match_info['bot_exit_reason']
        
        logger.info(f"   📊 Messages bot: {count}/{limit}")
        logger.info(f"   🚪 Exit reason: {exit_reason or 'N/A'}")
        
        # Check si déjà en exit
        if exit_reason:
            logger.warning(f"   ⚠️ Bot déjà en exit: {exit_reason}")
            logger.warning("   ❌ SKIP génération (conversation terminée)")
            await self.response_cache.clear_generating(match_id)
            return
        
        # Check si limite atteinte
        if count >= limit:
            logger.warning(f"   ⚠️ Limite atteinte: {count}/{limit}")
            logger.warning("   🚪 Génération message d'exit au lieu de réponse normale")
            
            # Générer exit immédiatement
            should_exit, reason = await self.exit_manager.check_should_exit(
                match_id,
                self.supabase
            )
            
            if should_exit:
                logger.info(f"   📝 Exit confirmé: {reason}")
                
                exit_messages = self.exit_manager.generate_exit_sequence(reason)
                
                logger.info(f"\n📤 Envoi séquence exit ({len(exit_messages)} messages)...")
                
                for i, exit_msg in enumerate(exit_messages, 1):
                    delay = exit_msg['delay']
                    logger.info(f"   ⏳ Attente {delay}s avant msg {i}...")
                    await asyncio.sleep(delay)
                    
                    await self.activate_typing(bot_id, match_id)
                    
                    typing_time = timing_engine.calculate_typing_time(exit_msg['text'])
                    logger.info(f"   ⌨️ Frappe {typing_time}s: {exit_msg['text'][:50]}...")
                    await asyncio.sleep(typing_time)
                    
                    await self.send_message(match_id, bot_id, exit_msg['text'])
                    logger.info(f"   ✅ Exit message {i} envoyé")
                    
                    await self.deactivate_typing(bot_id, match_id)
                
                await self.exit_manager.mark_as_exited(match_id, reason, self.supabase)
                
                logger.info("   🎯 Bot a quitté la conversation (limite atteinte)")
            
            # Cleanup et stop
            await self.response_cache.clear_generating(match_id)
            return
        
        logger.info("   ✅ Limite OK, génération autorisée")
        
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
        # 🆕 DÉMARRAGE MONITORING CONTINU
        # =============================
        
        base_message_count = len(context['history'])
        logger.info(f"\n👁️  Démarrage monitoring continu (base: {base_message_count})")
        
        await self.continuous_monitor.start(
            match_id=match_id,
            base_message_count=base_message_count,
            check_interval=2.0  # Vérifier toutes les 2 secondes
        )
        
        # =============================
        # PHASE 3: TIMING - RÉFLEXION
        # =============================
        logger.info("\n⏱️  Phase 3: Calcul timing...")
        
        thinking_delay = timing_engine.calculate_thinking_delay(
            analysis,
            len(user_message),
            context['time_since_last_bot_minutes'] * 60
        )
        
        logger.info(f"   Délai réflexion: {thinking_delay}s")
        logger.info(f"⏳ Attente {thinking_delay}s (temps de réflexion)...")
        
        # Attendre PENDANT QUE le monitoring tourne en background
        await asyncio.sleep(thinking_delay)
        
        # ============================================
        # 🆕 CHECKPOINT 1: Nouveaux messages pendant réflexion ?
        # ============================================
        
        if self.continuous_monitor.has_new_messages():
            logger.warning("⚠️ Nouveaux messages pendant réflexion → ANNULATION")
            logger.info("📨 Message repoussé pour retraitement complet")
            
            # Arrêter monitoring
            await self.continuous_monitor.stop()
            
            # 🔧 CRITICAL: Clear cache génération
            await self.response_cache.clear_generating(match_id)
            logger.info("🧹 Cache génération cleared (annulation)")
            
            # Repousser
            await asyncio.sleep(3)
            event_data['retry_count'] = event_data.get('retry_count', 0) + 1
            if event_data['retry_count'] <= 5:
                await self.redis_client.rpush('bot_messages', json.dumps(event_data))
            else:
                logger.warning("❌ Trop de retry")
            
            return  # STOP
        
        logger.info("✅ Pas de nouveaux messages pendant réflexion")
        
        # =============================
        # PHASE 4: ACTIVATION TYPING
        # =============================
        logger.info("\n⌨️  Phase 4: Activation typing...")
        await self.activate_typing(bot_id, match_id)
        
        # =============================
        # PHASE 5: GÉNÉRATION RÉPONSE
        # =============================
        logger.info("\n🧠 Phase 5: Génération réponse IA...")
        
        # 🆕 Enrichir prompt si USER_CONFUSED
        clarification_context = None
        if urgency_check.get('urgent') and urgency_check['context'] == 'USER_CONFUSED':
            clarification_context = {
                'last_bot_message': [m for m in context['history'] if m.get('profiles', {}).get('id') == bot_id][-1]['content'] if any(m.get('profiles', {}).get('id') == bot_id for m in context['history']) else None,
                'confused_messages': [m['content'] for m in context['history'][-3:] if m.get('profiles', {}).get('id') != bot_id]
            }
            logger.info(f"💡 Ajout contexte clarification: {clarification_context}")
        
        prompt = prompt_builder.build_full_prompt(
            context['bot_profile'],
            context['memory'],
            context['history'],
            user_message,
            analysis,
            clarification_context=clarification_context
        )
        
        response = self.generate_response(
            prompt,
            context['bot_profile'].get('temperature', 0.8)
        )
        
        logger.info(f"✅ Réponse: {response[:100]}...")
        
        # Check doublon après génération
        is_duplicate = await self.response_cache.is_duplicate_response(
            match_id,
            response
        )
        
        if is_duplicate:
            logger.error("❌ Réponse est un DOUBLON!")
            await self.response_cache.clear_generating(match_id)
            await self.continuous_monitor.stop()
            await self.deactivate_typing(bot_id, match_id)
            return
        
        # ============================================
        # 🆕 CHECKPOINT 2: Nouveaux messages après génération ?
        # ============================================
        
        if self.continuous_monitor.has_new_messages():
            logger.warning("⚠️ Nouveaux messages après génération → ANNULATION")
            logger.info("📨 Message repoussé")
            
            await self.continuous_monitor.stop()
            await self.deactivate_typing(bot_id, match_id)
            
            # 🔧 CRITICAL: Clear cache génération
            await self.response_cache.clear_generating(match_id)
            logger.info("🧹 Cache génération cleared (annulation)")
            
            await asyncio.sleep(3)
            event_data['retry_count'] = event_data.get('retry_count', 0) + 1
            if event_data['retry_count'] <= 5:
                await self.redis_client.rpush('bot_messages', json.dumps(event_data))
            else:
                logger.warning("❌ Trop de retry")
            
            return  # STOP
        
        logger.info("✅ Pas de nouveaux messages, on peut envoyer")
        
        # Parser messages (force un seul pour éviter contradictions)
        messages_to_send = [response.replace('|||', ' ')]
        logger.info("   ➡️ Un seul message (split désactivé)")
        
        # =============================
        # PHASE 6: ENVOI AVEC MONITORING CONTINU
        # =============================
        logger.info(f"\n📤 Phase 6: Envoi {len(messages_to_send)} message(s)...")
        
        # Stocker dans cache avant envoi
        await self.response_cache.store_response(
            match_id,
            response,
            user_message
        )
        
        for i, msg in enumerate(messages_to_send):
            # ============================================
            # 🆕 VÉRIFIER AVANT CHAQUE MESSAGE
            # ============================================
            
            if self.continuous_monitor.has_new_messages():
                logger.warning(f"⚠️ Nouveaux messages avant msg {i+1} → ANNULATION")
                await self.continuous_monitor.stop()
                await self.deactivate_typing(bot_id, match_id)
                
                # 🔧 CRITICAL: Clear cache génération
                await self.response_cache.clear_generating(match_id)
                logger.info("🧹 Cache génération cleared (annulation)")
                
                # Repousser
                await asyncio.sleep(3)
                event_data['retry_count'] = event_data.get('retry_count', 0) + 1
                if event_data['retry_count'] <= 5:
                    await self.redis_client.rpush('bot_messages', json.dumps(event_data))
                
                return  # STOP
            
            # Calculer temps frappe
            typing_time = timing_engine.calculate_typing_time(msg)
            logger.info(f"   ⏱️ Frappe msg {i+1}: {typing_time}s")
            
            # ============================================
            # 🆕 ATTENDRE PENDANT QUE MONITORING TOURNE
            # ============================================
            await asyncio.sleep(typing_time)
            
            # ============================================
            # 🆕 VÉRIFIER JUSTE AVANT ENVOI
            # ============================================
            
            if self.continuous_monitor.has_new_messages():
                logger.warning(f"⚠️ Nouveaux messages juste avant envoi → ANNULATION")
                await self.continuous_monitor.stop()
                await self.deactivate_typing(bot_id, match_id)
                
                # 🔧 CRITICAL: Clear cache génération
                await self.response_cache.clear_generating(match_id)
                logger.info("🧹 Cache génération cleared (annulation)")
                
                await asyncio.sleep(3)
                event_data['retry_count'] = event_data.get('retry_count', 0) + 1
                if event_data['retry_count'] <= 5:
                    await self.redis_client.rpush('bot_messages', json.dumps(event_data))
                
                return  # STOP
            
            # Envoyer
            await self.send_message(match_id, bot_id, msg)
            
            # Désactiver typing
            await self.deactivate_typing(bot_id, match_id)
            
            # Pause entre messages si plusieurs
            if i < len(messages_to_send) - 1:
                pause = timing_engine.calculate_pause_between_messages(len(msg))
                logger.info(f"   ⏸️ Pause: {pause}s")
                await asyncio.sleep(pause)
                await self.activate_typing(bot_id, match_id)
        
        # ============================================
        # 🆕 ARRÊTER MONITORING
        # ============================================
        
        await self.continuous_monitor.stop()
        
        logger.info("\n✅ Message traité avec succès !")
        
        # Cleanup cache
        await self.response_cache.clear_generating(match_id)
        
        # =============================
        # PHASE 7: VÉRIFICATION EXIT
        # =============================
        logger.info("\n🚪 Phase 7: Vérification exit...")
        
        should_exit, exit_reason = await self.exit_manager.check_should_exit(
            match_id, 
            self.supabase
        )
        
        if should_exit:
            logger.info(f"   ⚠️ Bot doit quitter: {exit_reason}")
            
            exit_messages = self.exit_manager.generate_exit_sequence(exit_reason)
            
            logger.info(f"\n📤 Envoi séquence exit ({len(exit_messages)} messages)...")
            
            for i, exit_msg in enumerate(exit_messages, 1):
                delay = exit_msg['delay']
                logger.info(f"   ⏳ Attente {delay}s avant msg {i}...")
                await asyncio.sleep(delay)
                
                await self.activate_typing(bot_id, match_id)
                
                typing_time = timing_engine.calculate_typing_time(exit_msg['text'])
                logger.info(f"   ⌨️ Frappe {typing_time}s: {exit_msg['text'][:50]}...")
                await asyncio.sleep(typing_time)
                
                await self.send_message(match_id, bot_id, exit_msg['text'])
                logger.info(f"   ✅ Exit message {i} envoyé")
                
                await self.deactivate_typing(bot_id, match_id)
            
            await self.exit_manager.mark_as_exited(match_id, exit_reason, self.supabase)
            
            logger.info("   🎯 Bot a quitté la conversation")
        else:
            logger.info("   ✅ Pas d'exit pour ce message")
    
    async def run(self):
        """Lance le worker"""
        try:
            # Connexions
            await self.connect_supabase()
            await self.connect_redis()
            self.connect_openai()
            
            logger.info("=" * 60)
            logger.info("🧠 WORKER INTELLIGENCE V3.0 ACTIF")
            logger.info("   ✅ Lock Redis distribué")
            logger.info("   ✅ Monitoring continu")
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
            if self.supabase:
                await self.supabase.close()


async def main():
    """Point d'entrée"""
    worker = WorkerIntelligence()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
