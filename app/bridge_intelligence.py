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
from app.match_monitor import MatchMonitor
from app.supabase_client import SupabaseClient
import logging

logger = logging.getLogger(__name__)


class BridgeIntelligence:
    """Bridge avec grouping intelligent + cooldown anti-duplication"""
    
    def __init__(self):
        self.pg_conn = None
        self.redis_client = None
        self.context_manager = None
        self.match_monitor = None
        self.supabase_client = None
        self.running = False
        self.GROUPING_DELAY = 15  # Secondes (laisser temps à user de finir)
        
        # 🆕 COOLDOWN SYSTEM - Anti-duplication
        self.last_push_times: Dict[str, datetime] = {}  # {match_id: datetime}
        self.PUSH_COOLDOWN = 5  # Secondes - évite création jobs multiples
        
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
        
        # Créer SupabaseClient pour match_monitor
        self.supabase_client = SupabaseClient()
        await self.supabase_client.connect()
        
        self.match_monitor = MatchMonitor(self.supabase_client)
        logger.info("✅ Connecté à Redis")
    
    async def push_to_queue(self, message: Dict, max_retries: int = 3):
        """Pousse un message dans la queue avec retry automatique"""
        queue_key = "bot_messages"
        
        for attempt in range(max_retries):
            try:
                await self.redis_client.rpush(queue_key, json.dumps(message))
                logger.info(f"✅ Message poussé dans queue")
                return  # Succès
                
            except redis.ConnectionError as e:
                logger.warning(f"⚠️ Tentative {attempt + 1}/{max_retries} - Connexion Redis perdue: {e}")
                
                if attempt < max_retries - 1:
                    # Attendre avant retry (backoff exponentiel)
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.info(f"⏳ Retry dans {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    
                    # Tenter reconnexion Redis
                    try:
                        logger.info("🔄 Reconnexion Redis...")
                        await self.redis_client.close()
                        self.redis_client = await redis.from_url(
                            settings.redis_url,
                            encoding="utf-8",
                            decode_responses=True
                        )
                        self.context_manager = RedisContextManager(self.redis_client)
                        logger.info("✅ Reconnexion Redis réussie")
                    except Exception as reconnect_error:
                        logger.error(f"❌ Reconnexion Redis échouée: {reconnect_error}")
                else:
                    # Dernière tentative échouée
                    logger.error(f"❌ Échec définitif après {max_retries} tentatives")
                    raise
                    
            except Exception as e:
                logger.error(f"❌ Erreur inattendue push_to_queue: {type(e).__name__}: {e}")
                raise
    
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
            
            # 🆕 ENREGISTRER TEMPS DU PUSH - Active cooldown
            self.last_push_times[match_id] = datetime.now()
            logger.info(f"⏰ Cooldown activé pour {self.PUSH_COOLDOWN}s")
            
            # Nettoyer contexte
            await self.context_manager.delete_context(match_id)
    
    async def handle_notification(self, connection, pid, channel, payload):
        """
        Callback PostgreSQL NOTIFY avec grouping intelligent + cooldown
        """
        try:
            logger.info(f"📨 Notification reçue (pid={pid}, channel={channel})")
            logger.debug(f"   Payload: {payload[:200]}...")  # Log premiers 200 chars
            
            message = json.loads(payload)
            match_id = message['match_id']
            logger.debug(f"   Match ID: {match_id}")
            
            # 🆕 CHECK COOLDOWN - Évite jobs multiples pour messages rapprochés
            last_push = self.last_push_times.get(match_id)
            if last_push:
                time_since = (datetime.now() - last_push).total_seconds()
                if time_since < self.PUSH_COOLDOWN:
                    logger.info(f"⏸️ Cooldown actif ({time_since:.1f}s), ajout au prochain groupe")
                    # Ajouter au contexte sans créer de timer
                    context = await self.context_manager.get_context(match_id)
                    if context:
                        await self.context_manager.update_context(match_id, message)
                        logger.info(f"   📝 Message ajouté au contexte existant")
                    return  # Ne pas créer de nouveau timer
            
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
                    
                    # Si timer pas encore démarré, le démarrer maintenant
                    # NE PAS redémarrer pour éviter délais infinis si user tape lentement
                    if not context.get('timer_started'):
                        logger.info(f"⏰ Démarrage timer grouping {self.GROUPING_DELAY}s")
                        asyncio.create_task(self.delayed_push(match_id))
                        context['timer_started'] = True
                        await self.context_manager.set_context(match_id, context)
                    else:
                        logger.info("   ⏰ Timer déjà actif, pas de redémarrage")
                    
                    return  # Ne pas pousser maintenant
            
            # Nouveau contexte : démarrer grouping (ne PAS pousser immédiatement)
            context = await self.context_manager.init_context(match_id, message)
            
            # Démarrer timer pour voir si d'autres messages suivent
            logger.info(f"⏰ Nouveau message, démarrage timer {self.GROUPING_DELAY}s")
            asyncio.create_task(self.delayed_push(match_id))
            
            # Marquer timer comme démarré
            context['timer_started'] = True
            await self.context_manager.set_context(match_id, context)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur parsing JSON payload: {e}")
            logger.error(f"   Payload reçu: {payload}")
        except KeyError as e:
            logger.error(f"❌ Clé manquante dans payload: {e}")
            logger.error(f"   Message: {message}")
        except Exception as e:
            logger.error(f"❌ Erreur inattendue dans handle_notification: {type(e).__name__}: {e}")
            logger.exception("Stack trace complet:")  # Log full stack trace
    
    async def handle_new_match(self, connection, pid, channel, payload):
        """
        Callback PostgreSQL NOTIFY pour nouveaux matchs
        """
        try:
            logger.info(f"🔍 Nouveau match détecté")
            
            match_data = json.loads(payload)
            
            # Passer le Dict complet à match_monitor
            # Il identifiera lui-même qui est le bot
            await self.match_monitor.process_new_match(match_data)
            
        except Exception as e:
            logger.error(f"❌ Erreur nouveau match: {e}")
    
    async def start_listening(self):
        """Démarre l'écoute PostgreSQL"""
        logger.info("👂 Démarrage écoute 'bot_events' et 'new_match'...")
        
        await self.pg_conn.add_listener('bot_events', self.handle_notification)
        await self.pg_conn.add_listener('new_match', self.handle_new_match)
        
        logger.info("✅ Écoute active (messages + nouveaux matchs)")
        logger.info("⏳ En attente...")
        
        self.running = True
        
        # Compteur pour keepalive
        keepalive_counter = 0
        
        try:
            while self.running:
                await asyncio.sleep(1)
                
                # Keepalive toutes les 30 secondes
                keepalive_counter += 1
                if keepalive_counter >= 30:
                    try:
                        # Simple query pour garder connexion active
                        await self.pg_conn.fetchval('SELECT 1')
                        logger.debug("💓 Keepalive PostgreSQL")
                        keepalive_counter = 0
                    except Exception as e:
                        logger.error(f"❌ Keepalive échoué, reconnexion...")
                        # Reconnexion
                        await self.reconnect()
                        keepalive_counter = 0
                        
        except KeyboardInterrupt:
            await self.stop()
    
    async def reconnect(self):
        """Reconnecte au PostgreSQL si connexion perdue"""
        try:
            logger.warning("🔄 Reconnexion PostgreSQL...")
            
            # Fermer ancienne connexion
            if self.pg_conn:
                await self.pg_conn.close()
            
            # Nouvelle connexion
            await self.connect_postgres()
            
            # Re-setup listeners
            await self.pg_conn.add_listener('bot_events', self.handle_notification)
            await self.pg_conn.add_listener('new_match', self.handle_new_match)
            
            logger.info("✅ Reconnexion réussie")
            
        except Exception as e:
            logger.error(f"❌ Reconnexion échouée: {e}")
            # Retry dans 5s
            await asyncio.sleep(5)
            await self.reconnect()
    
    async def stop(self):
        """Arrête le bridge"""
        logger.info("🛑 Arrêt bridge...")
        self.running = False
        
        if self.pg_conn:
            await self.pg_conn.remove_listener('bot_events', self.handle_notification)
            await self.pg_conn.remove_listener('new_match', self.handle_new_match)
            await self.pg_conn.close()
        
        if self.supabase_client:
            await self.supabase_client.close()
            
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
