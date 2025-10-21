"""
Module pour surveiller les nouveaux matchs et créer des initiations.
Décide si le bot envoie le premier message (40-60%) et planifie l'envoi.
"""
import logging
import asyncio
import random
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Optional

from app.initiation_builder import InitiationBuilder
from app.relance_builder import RelanceBuilder
from app.config import Config
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class MatchMonitor:
    """Surveille les nouveaux matchs et crée des initiations bot"""
    
    def __init__(self, supabase_client, redis_client=None):
        """
        Args:
            supabase_client: Notre SupabaseClient custom (asyncpg)
            redis_client: Client Redis pour pusher relances
        """
        self.supabase = supabase_client
        self.redis_client = redis_client
        self.initiation_builder = InitiationBuilder()
        self.relance_builder = RelanceBuilder()
        
        # Probabilité d'initiation (configurable)
        self.INITIATION_PROBABILITY = Config.INITIATION_PROBABILITY
        
        # Délais (configurable, immédiat en test)
        self.MIN_DELAY_MINUTES = Config.MIN_DELAY_MINUTES
        self.MAX_DELAY_MINUTES = Config.MAX_DELAY_MINUTES
        
        # HTTP headers pour REST API
        # Debug: vérifier clé présente
        service_key = Config.SUPABASE_SERVICE_KEY
        if not service_key:
            logger.error("❌ SUPABASE_SERVICE_KEY non définie dans Config!")
        else:
            logger.info(f"🔑 Service key chargée: {service_key[:20]}...")
        
        self.rest_headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    async def process_new_match(self, match: Dict) -> Optional[str]:
        """
        Traite un nouveau match : décide d'initier et crée l'initiation.
        
        Args:
            match: Dict avec user1_id, user2_id, id, created_at
            
        Returns:
            str: ID de l'initiation créée, ou None si pas d'initiation
        """
        try:
            # Identifier qui est le bot
            bot_id, user_id = self._identify_bot_and_user(match)
            
            if not bot_id:
                logger.debug("Match ne contient pas de bot, skip")
                return None
            
            # ✅ CRITIQUE : Vérifier si conversation existe déjà
            existing_messages = await self._check_existing_messages(match['id'])
            if existing_messages > 0:
                logger.info(
                    f"🚫 Match {match['id']} a déjà {existing_messages} message(s), "
                    f"pas d'initiation (conversation déjà lancée par user)"
                )
                return None
            
            # Décision : faut-il initier ?
            if not self._should_initiate():
                logger.info(f"🎲 Pas d'initiation pour match {match['id']} (probabilité)")
                return None
            
            # Calculer délai
            delay_minutes = self._calculate_delay()
            scheduled_for = datetime.now() + timedelta(minutes=delay_minutes)
            
            if Config.TEST_MODE:
                logger.info(f"🧪 TEST MODE: Initiation immédiate pour match {match['id']}")
            else:
                logger.info(
                    f"📅 Initiation planifiée dans {delay_minutes}min "
                    f"({scheduled_for.strftime('%H:%M')})"
                )
            
            # Charger profils
            bot_profile = await self._load_profile(bot_id)
            user_profile = await self._load_profile(user_id)
            
            # Générer premier message
            first_message = self.initiation_builder.build_first_message(
                bot_profile, user_profile
            )
            
            # Créer initiation dans DB
            initiation_id = await self._create_initiation(
                match_id=match['id'],
                bot_id=bot_id,
                user_id=user_id,
                scheduled_for=scheduled_for,
                first_message=first_message
            )
            
            logger.info(
                f"✅ Initiation créée : {initiation_id}\n"
                f"   Bot: {bot_profile['first_name']}\n"
                f"   User: {user_profile['first_name']}\n"
                f"   Message: {first_message[:50]}...\n"
                f"   Envoi: {scheduled_for.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            return initiation_id
            
        except Exception as e:
            logger.error(f"❌ Erreur process_new_match: {e}", exc_info=True)
            return None
    
    def _identify_bot_and_user(self, match: Dict) -> tuple:
        """Identifie qui est le bot dans le match"""
        bot_ids = [Config.BOT_CAMILLE_ID, Config.BOT_PAUL_ID]
        bot_ids = [b for b in bot_ids if b]  # Filter None
        
        user1_id = match['user1_id']
        user2_id = match['user2_id']
        
        if user1_id in bot_ids:
            return user1_id, user2_id
        elif user2_id in bot_ids:
            return user2_id, user1_id
        
        return None, None
    
    def _should_initiate(self) -> bool:
        """Décide si le bot doit initier (probabilité 40-60%)"""
        return random.random() < self.INITIATION_PROBABILITY
    
    def _calculate_delay(self) -> int:
        """
        Calcule délai en minutes.
        Distribution triangulaire : pic au milieu de la plage.
        """
        # Pic au milieu de MIN et MAX
        mode = (self.MIN_DELAY_MINUTES + self.MAX_DELAY_MINUTES) / 2
        
        delay = int(random.triangular(
            self.MIN_DELAY_MINUTES,
            self.MAX_DELAY_MINUTES,
            mode
        ))
        
        return delay
    
    async def _load_profile(self, profile_id: str) -> Dict:
        """Charge un profil complet via REST API"""
        try:
            async with httpx.AsyncClient() as client:
                # Profile
                url = f"{Config.SUPABASE_URL}/rest/v1/profiles"
                params = {
                    "id": f"eq.{profile_id}",
                    "select": "id,first_name,birth_date,bio,city,department,hiking_level,photos"
                }
                resp = await client.get(url, headers=self.rest_headers, params=params)
                resp.raise_for_status()
                profiles = resp.json()
                
                if not profiles:
                    raise ValueError(f"Profile {profile_id} not found")
                
                profile = profiles[0]
                
                # Interests
                url = f"{Config.SUPABASE_URL}/rest/v1/user_interests"
                params = {
                    "user_id": f"eq.{profile_id}",
                    "select": "interests(name)"
                }
                resp = await client.get(url, headers=self.rest_headers, params=params)
                resp.raise_for_status()
                interests_data = resp.json()
                
                profile['interests'] = [
                    i['interests']['name'] 
                    for i in interests_data
                    if i.get('interests')
                ]
                
                return profile
            
        except Exception as e:
            logger.error(f"Erreur load_profile {profile_id}: {e}")
            return {
                'id': profile_id,
                'first_name': 'Utilisateur',
                'interests': []
            }
    
    async def _check_existing_messages(self, match_id: str) -> int:
        """
        Vérifie s'il y a déjà eu des messages dans ce match.
        
        Args:
            match_id: ID du match
            
        Returns:
            int: Nombre de messages existants (0 si aucun)
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{Config.SUPABASE_URL}/rest/v1/messages"
                params = {
                    "match_id": f"eq.{match_id}",
                    "select": "id"
                }
                
                resp = await client.get(url, headers=self.rest_headers, params=params)
                resp.raise_for_status()
                messages = resp.json()
                
                return len(messages)
        except Exception as e:
            logger.error(f"Erreur check_existing_messages: {e}")
            return 0  # Sécurité : si erreur, on suppose 0 messages
    
    async def _create_initiation(
        self,
        match_id: str,
        bot_id: str,
        user_id: str,
        scheduled_for: datetime,
        first_message: str
    ) -> str:
        """Crée une entrée dans bot_initiations via REST API"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"{Config.SUPABASE_URL}/rest/v1/bot_initiations"
                payload = {
                    'match_id': match_id,
                    'bot_id': bot_id,
                    'user_id': user_id,
                    'scheduled_for': scheduled_for.isoformat(),
                    'first_message': first_message,
                    'status': 'pending'
                }
                
                resp = await client.post(
                    url, 
                    headers=self.rest_headers, 
                    json=payload
                )
                resp.raise_for_status()
                result = resp.json()
                
                return result[0]['id']
            
        except Exception as e:
            logger.error(f"Erreur create_initiation: {e}")
            raise
    
    async def check_pending_initiations(self):
        """
        Vérifie les initiations en attente et envoie celles dont l'heure est venue.
        À appeler régulièrement (ex: toutes les 30s).
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{Config.SUPABASE_URL}/rest/v1/bot_initiations"
                params = {
                    "status": "eq.pending",
                    "scheduled_for": f"lte.{datetime.now().isoformat()}",
                    "select": "*"
                }
                
                resp = await client.get(url, headers=self.rest_headers, params=params)
                resp.raise_for_status()
                pending = resp.json()
                
                if not pending:
                    return
                
                logger.info(f"📬 {len(pending)} initiation(s) à envoyer")
                
                for initiation in pending:
                    await self._send_initiation(initiation)
                
        except Exception as e:
            logger.error(f"❌ Erreur check_pending_initiations: {e}")
    
    async def _send_initiation(self, initiation: Dict):
        """Envoie le premier message et met à jour l'initiation via REST API"""
        try:
            async with httpx.AsyncClient() as client:
                # ✅ Vérifier si DES MESSAGES EXISTENT (user OU bot)
                url = f"{Config.SUPABASE_URL}/rest/v1/messages"
                params = {
                    "match_id": f"eq.{initiation['match_id']}",
                    # On ne filtre PAS par sender_id → vérifie TOUS les messages
                    "select": "id",
                    "limit": "1"
                }
                
                resp = await client.get(url, headers=self.rest_headers, params=params)
                resp.raise_for_status()
                messages = resp.json()
                
                if messages:
                    # Conversation existe déjà, annuler initiation
                    logger.info(f"🚫 Initiation {initiation['id']} annulée (conversation existe déjà)")
                    
                    url = f"{Config.SUPABASE_URL}/rest/v1/bot_initiations"
                    params = {"id": f"eq.{initiation['id']}"}
                    payload = {"status": "cancelled"}
                    
                    await client.patch(
                        url, 
                        headers=self.rest_headers, 
                        params=params,
                        json=payload
                    )
                    
                    return
                
                # Envoyer le message
                url = f"{Config.SUPABASE_URL}/rest/v1/messages"
                payload = {
                    'match_id': initiation['match_id'],
                    'sender_id': initiation['bot_id'],
                    'content': initiation['first_message'],
                    'status': 'sent'
                }
                
                await client.post(url, headers=self.rest_headers, json=payload)
                
                # Update initiation status
                url = f"{Config.SUPABASE_URL}/rest/v1/bot_initiations"
                params = {"id": f"eq.{initiation['id']}"}
                payload = {
                    'status': 'sent',
                    'sent_at': datetime.now().isoformat()
                }
                
                await client.patch(
                    url,
                    headers=self.rest_headers,
                    params=params,
                    json=payload
                )
                
                logger.info(
                    f"✅ Premier message envoyé : {initiation['id']}\n"
                    f"   Message: {initiation['first_message']}"
                )
            
        except Exception as e:
            logger.error(f"❌ Erreur send_initiation {initiation['id']}: {e}")
    
    async def check_abandoned_conversations(self):
        """
        Détecte conversations où user a envoyé message sans réponse depuis 2-4h.
        Génère une relance naturelle et pousse dans queue Redis.
        
        À appeler régulièrement (ex: toutes les 30-60s).
        """
        if not self.redis_client:
            logger.warning("Redis client non disponible, skip abandoned check")
            return
        
        try:
            # Chercher matches actifs où dernier message = user
            query = """
            WITH last_messages AS (
                SELECT DISTINCT ON (match_id)
                    match_id,
                    sender_id,
                    created_at,
                    content
                FROM messages
                WHERE match_id IN (
                    SELECT id FROM matches 
                    WHERE bot_exited_at IS NULL
                )
                ORDER BY match_id, created_at DESC
            )
            SELECT 
                lm.match_id,
                lm.sender_id,
                lm.created_at as last_message_at,
                lm.content as last_message_content,
                m.user1_id,
                m.user2_id,
                EXTRACT(EPOCH FROM (NOW() - lm.created_at))/3600 as hours_since
            FROM last_messages lm
            JOIN matches m ON m.id = lm.match_id
            WHERE 
                -- Dernier message il y a 2-48h
                lm.created_at < NOW() - INTERVAL '2 hours'
                AND lm.created_at > NOW() - INTERVAL '48 hours'
                -- Sender n'est pas un bot
                AND lm.sender_id NOT IN ($1, $2)
            ORDER BY lm.created_at ASC
            LIMIT 5
            """
            
            # Positional params pour asyncpg
            bot_ids = [
                Config.BOT_CAMILLE_ID or '', 
                Config.BOT_PAUL_ID or ''
            ]
            
            abandoned = await self.supabase.fetch(query, *bot_ids)
            
            if not abandoned:
                return
            
            logger.info(f"🔍 {len(abandoned)} conversation(s) potentiellement abandonnée(s)")
            
            for conv in abandoned:
                await self._process_abandoned_conversation(conv)
                
        except Exception as e:
            logger.error(f"❌ Erreur check_abandoned_conversations: {e}", exc_info=True)
    
    async def _process_abandoned_conversation(self, conv: Dict):
        """
        Traite une conversation abandonnée : vérifie + génère relance.
        
        Args:
            conv: Dict avec match_id, sender_id, hours_since, etc.
        """
        try:
            match_id = conv['match_id']
            hours_since = conv['hours_since']
            
            logger.info(f"📋 Conversation {match_id}: dernier msg il y a {hours_since:.1f}h")
            
            # Identifier bot et user
            bot_id, user_id = self._identify_bot_and_user({
                'user1_id': conv['user1_id'],
                'user2_id': conv['user2_id']
            })
            
            if not bot_id:
                logger.debug(f"Match {match_id} ne contient pas de bot, skip")
                return
            
            # Vérifier si déjà relancé récemment (check dans Redis)
            last_relance_key = f"last_relance:{match_id}"
            last_relance = await self.redis_client.get(last_relance_key)
            
            last_relance_hours = None
            if last_relance:
                last_relance_timestamp = float(last_relance)
                last_relance_hours = (datetime.now().timestamp() - last_relance_timestamp) / 3600
            
            # Décider si relance nécessaire
            if not self.relance_builder.should_send_relance(hours_since, last_relance_hours):
                logger.info(f"Pas de relance nécessaire pour {match_id}")
                return
            
            logger.info(f"✅ Relance nécessaire pour {match_id}")
            
            # Charger profils
            bot_profile = await self._load_profile(bot_id)
            user_profile = await self._load_profile(user_id)
            
            # Générer message de relance
            relance_message = self.relance_builder.build_relance_message(
                bot_profile,
                user_profile,
                hours_since
            )
            
            # Créer event pour queue Redis
            event_data = {
                'match_id': match_id,
                'bot_id': bot_id,
                'sender_id': user_id,
                'message_content': relance_message,
                'type': 'relance',
                'hours_since_last': hours_since
            }
            
            # Push dans queue
            await self.redis_client.rpush(
                'bot_messages',
                json.dumps(event_data)
            )
            
            # Marquer relance envoyée (TTL 48h)
            await self.redis_client.setex(
                last_relance_key,
                48 * 3600,  # 48h
                str(datetime.now().timestamp())
            )
            
            logger.info(
                f"✅ Relance poussée dans queue: {match_id}\n"
                f"   Bot: {bot_profile['first_name']}\n"
                f"   User: {user_profile['first_name']}\n"
                f"   Délai: {hours_since:.1f}h\n"
                f"   Message: {relance_message}"
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur process_abandoned {conv.get('match_id')}: {e}", exc_info=True)
