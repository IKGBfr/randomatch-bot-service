"""
Pre-Processing - Vérifications avant de générer une réponse

- Vérifie si user tape encore
- Charge historique complet
- Charge mémoire bot
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from supabase import Client
import logging

logger = logging.getLogger(__name__)


class PreProcessor:
    """Gère les vérifications et chargements avant génération"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.MAX_HISTORY_MESSAGES = 50
        self.TYPING_CHECK_DELAY = 2  # Secondes
    
    async def check_user_typing(
        self,
        match_id: str,
        user_id: str,
        max_retries: int = 1
    ) -> bool:
        """
        Vérifie si l'user est en train de taper
        
        Args:
            match_id: ID du match
            user_id: ID de l'utilisateur
            max_retries: Nombre de re-vérifications
            
        Returns:
            True si user tape encore, False sinon
        """
        for attempt in range(max_retries + 1):
            try:
                # Récupérer événement typing
                result = self.supabase.table('typing_events').select('*').eq(
                    'user_id', user_id
                ).eq(
                    'match_id', match_id
                ).maybe_single().execute()
                
                if result.data and result.data.get('is_typing'):
                    logger.info(f"👤 User tape encore (attempt {attempt + 1}/{max_retries + 1})")
                    
                    # Si pas dernier attempt, attendre et re-vérifier
                    if attempt < max_retries:
                        await asyncio.sleep(self.TYPING_CHECK_DELAY)
                        continue
                    
                    return True  # User tape toujours
                
                # User ne tape pas
                return False
                
            except Exception as e:
                logger.error(f"❌ Erreur check typing: {e}")
                return False  # En cas d'erreur, continuer
        
        return False
    
    def fetch_conversation_history(
        self,
        match_id: str,
        limit: int = None
    ) -> List[Dict]:
        """
        Récupère l'historique complet de la conversation
        
        Args:
            match_id: ID du match
            limit: Nombre max de messages (défaut: MAX_HISTORY_MESSAGES)
            
        Returns:
            Liste de messages ordonnés (plus ancien → plus récent)
        """
        try:
            if limit is None:
                limit = self.MAX_HISTORY_MESSAGES
            
            # Récupérer messages avec infos sender
            result = self.supabase.table('messages').select(
                'id, content, sender_id, created_at, type, profiles!messages_sender_id_fkey(first_name, is_bot)'
            ).eq(
                'match_id', match_id
            ).order(
                'created_at', desc=False  # Plus ancien d'abord
            ).limit(limit).execute()
            
            if not result.data:
                logger.warning(f"⚠️  Aucun message dans historique")
                return []
            
            # Formater messages
            messages = []
            for msg in result.data:
                profile = msg.get('profiles', {})
                messages.append({
                    'id': msg['id'],
                    'content': msg['content'],
                    'sender_id': msg['sender_id'],
                    'sender_name': profile.get('first_name', 'Unknown'),
                    'is_bot': profile.get('is_bot', False),
                    'created_at': msg['created_at'],
                    'type': msg.get('type', 'text')
                })
            
            logger.info(f"📚 Historique chargé: {len(messages)} messages")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Erreur fetch history: {e}")
            return []
    
    def fetch_bot_memory(
        self,
        bot_id: str,
        user_id: str
    ) -> Optional[Dict]:
        """
        Récupère la mémoire du bot pour cet utilisateur
        
        Args:
            bot_id: ID du bot
            user_id: ID de l'utilisateur
            
        Returns:
            Dict avec mémoire ou None
        """
        try:
            result = self.supabase.table('bot_memory').select('*').eq(
                'bot_id', bot_id
            ).eq(
                'user_id', user_id
            ).maybe_single().execute()
            
            if result.data:
                logger.info(f"🧠 Mémoire chargée (trust: {result.data.get('trust_score', 0)})")
                return result.data
            else:
                logger.info(f"🆕 Pas de mémoire existante (première conversation)")
                return self._create_default_memory(bot_id, user_id)
                
        except Exception as e:
            logger.error(f"❌ Erreur fetch memory: {e}")
            return self._create_default_memory(bot_id, user_id)
    
    def _create_default_memory(self, bot_id: str, user_id: str) -> Dict:
        """Crée une mémoire par défaut"""
        return {
            'bot_id': bot_id,
            'user_id': user_id,
            'user_name': None,
            'trust_score': 0,
            'relationship_level': 'stranger',
            'conversation_tone': 'neutral',
            'preferred_topics': [],
            'topics_to_avoid': [],
            'important_facts': {},
            'total_messages_exchanged': 0
        }
    
    def fetch_bot_profile(self, bot_id: str) -> Optional[Dict]:
        """
        Récupère le profil du bot
        
        Args:
            bot_id: ID du bot
            
        Returns:
            Dict avec profil bot
        """
        try:
            result = self.supabase.table('bot_profiles').select(
                'system_prompt, bot_personality, temperature'
            ).eq('id', bot_id).single().execute()
            
            if result.data:
                logger.info(f"🤖 Bot profile chargé ({result.data.get('bot_personality')})")
                return result.data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur fetch bot profile: {e}")
            return None
    
    def calculate_time_since_last_bot_message(
        self,
        messages: List[Dict],
        bot_id: str
    ) -> float:
        """
        Calcule le temps depuis le dernier message du bot
        
        Args:
            messages: Liste des messages
            bot_id: ID du bot
            
        Returns:
            Minutes depuis dernier message bot (0 si aucun)
        """
        # Trouver dernier message bot
        bot_messages = [m for m in messages if m['sender_id'] == bot_id]
        
        if not bot_messages:
            return 0
        
        last_bot_msg = bot_messages[-1]
        last_time = datetime.fromisoformat(last_bot_msg['created_at'].replace('Z', '+00:00'))
        now = datetime.now(last_time.tzinfo)
        
        delta = (now - last_time).total_seconds() / 60  # Minutes
        
        return round(delta, 2)
    
    async def prepare_context(
        self,
        match_id: str,
        bot_id: str,
        user_id: str,
        check_typing: bool = True
    ) -> Tuple[bool, Dict]:
        """
        Prépare tout le contexte nécessaire
        
        Args:
            match_id: ID du match
            bot_id: ID du bot
            user_id: ID de l'user
            check_typing: Vérifier si user tape
            
        Returns:
            (should_wait, context_dict)
            - should_wait: True si doit attendre (user tape)
            - context_dict: Tout le contexte chargé
        """
        # 1. Check typing
        if check_typing:
            is_typing = await self.check_user_typing(match_id, user_id)
            if is_typing:
                logger.info("⏸️  User tape encore, on attend...")
                return True, {}
        
        # 2. Charger tout
        logger.info("📦 Chargement contexte complet...")
        
        history = self.fetch_conversation_history(match_id)
        memory = self.fetch_bot_memory(bot_id, user_id)
        bot_profile = self.fetch_bot_profile(bot_id)
        time_since_last = self.calculate_time_since_last_bot_message(history, bot_id)
        
        context = {
            'history': history,
            'memory': memory,
            'bot_profile': bot_profile,
            'time_since_last_bot_minutes': time_since_last,
            'conversation_length': len(history)
        }
        
        logger.info(f"✅ Contexte prêt ({len(history)} msgs, trust={memory.get('trust_score', 0)})")
        
        return False, context
