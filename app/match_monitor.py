"""
Module pour surveiller les nouveaux matchs et créer des initiations.
Décide si le bot envoie le premier message (40-60%) et planifie l'envoi.
"""
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Optional
from supabase import Client

from app.initiation_builder import InitiationBuilder
from app.config import Config

logger = logging.getLogger(__name__)

class MatchMonitor:
    """Surveille les nouveaux matchs et crée des initiations bot"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.initiation_builder = InitiationBuilder()
        
        # Probabilité d'initiation (configurable)
        self.INITIATION_PROBABILITY = Config.INITIATION_PROBABILITY
        
        # Délais (configurable, immédiat en test)
        self.MIN_DELAY_MINUTES = Config.MIN_DELAY_MINUTES
        self.MAX_DELAY_MINUTES = Config.MAX_DELAY_MINUTES
    
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
        Calcule délai en minutes (15min-6h).
        Distribution non uniforme : plus probable autour 1-2h.
        """
        # Distribution triangulaire : pic à 90min
        delay = int(random.triangular(
            self.MIN_DELAY_MINUTES,
            self.MAX_DELAY_MINUTES,
            90  # Mode (pic de probabilité)
        ))
        
        return delay
    
    async def _load_profile(self, profile_id: str) -> Dict:
        """Charge un profil complet depuis Supabase"""
        try:
            response = self.supabase.table('profiles').select(
                'id, first_name, birth_date, bio, city, department, '
                'hiking_level, photos'
            ).eq('id', profile_id).single().execute()
            
            profile = response.data
            
            # Charger intérêts
            interests_response = self.supabase.table('user_interests').select(
                'interests(name)'
            ).eq('user_id', profile_id).execute()
            
            profile['interests'] = [
                i['interests']['name'] 
                for i in interests_response.data
            ] if interests_response.data else []
            
            return profile
            
        except Exception as e:
            logger.error(f"Erreur load_profile {profile_id}: {e}")
            return {
                'id': profile_id,
                'first_name': 'Utilisateur',
                'interests': []
            }
    
    async def _create_initiation(
        self,
        match_id: str,
        bot_id: str,
        user_id: str,
        scheduled_for: datetime,
        first_message: str
    ) -> str:
        """Crée une entrée dans bot_initiations"""
        try:
            response = self.supabase.table('bot_initiations').insert({
                'match_id': match_id,
                'bot_id': bot_id,
                'user_id': user_id,
                'scheduled_for': scheduled_for.isoformat(),
                'first_message': first_message,
                'status': 'pending'
            }).execute()
            
            return response.data[0]['id']
            
        except Exception as e:
            logger.error(f"Erreur create_initiation: {e}")
            raise
    
    async def check_pending_initiations(self):
        """
        Vérifie les initiations en attente et envoie celles dont l'heure est venue.
        À appeler régulièrement (ex: toutes les minutes).
        """
        try:
            # Chercher initiations pending dont scheduled_for <= now
            response = self.supabase.table('bot_initiations').select(
                '*'
            ).eq('status', 'pending').lte(
                'scheduled_for', datetime.now().isoformat()
            ).execute()
            
            pending = response.data
            
            if not pending:
                return
            
            logger.info(f"📬 {len(pending)} initiation(s) à envoyer")
            
            for initiation in pending:
                await self._send_initiation(initiation)
                
        except Exception as e:
            logger.error(f"❌ Erreur check_pending_initiations: {e}")
    
    async def _send_initiation(self, initiation: Dict):
        """Envoie le premier message et met à jour l'initiation"""
        try:
            # Vérifier si user a déjà envoyé un message
            messages_response = self.supabase.table('messages').select(
                'id'
            ).eq('match_id', initiation['match_id']).eq(
                'sender_id', initiation['user_id']
            ).limit(1).execute()
            
            if messages_response.data:
                # User a envoyé en premier, annuler initiation
                logger.info(f"🚫 Initiation {initiation['id']} annulée (user a envoyé)")
                
                self.supabase.table('bot_initiations').update({
                    'status': 'cancelled'
                }).eq('id', initiation['id']).execute()
                
                return
            
            # Envoyer le message
            message_response = self.supabase.table('messages').insert({
                'match_id': initiation['match_id'],
                'sender_id': initiation['bot_id'],
                'content': initiation['first_message'],
                'status': 'sent'
            }).execute()
            
            # Update initiation status
            self.supabase.table('bot_initiations').update({
                'status': 'sent',
                'sent_at': datetime.now().isoformat()
            }).eq('id', initiation['id']).execute()
            
            logger.info(
                f"✅ Premier message envoyé : {initiation['id']}\n"
                f"   Message: {initiation['first_message']}"
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur send_initiation {initiation['id']}: {e}")
