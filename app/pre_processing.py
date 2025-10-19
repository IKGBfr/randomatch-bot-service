"""
Pre-Processing - Vérifications avant de générer une réponse

- Vérifie si user tape encore
- Charge historique complet
- Charge mémoire bot
"""

import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.supabase_client import SupabaseClient
import logging

logger = logging.getLogger(__name__)


class PreProcessor:
    """Gère les vérifications et chargements avant génération"""
    
    def __init__(self, supabase: SupabaseClient):
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
                result = await self.supabase.select(
                    'typing_events',
                    filters={'user_id': user_id, 'match_id': match_id}
                )
                
                if result and len(result) > 0:
                    typing_event = result[0]
                    is_typing = typing_event.get('is_typing', False)
                    
                    if is_typing and attempt < max_retries:
                        await asyncio.sleep(self.TYPING_CHECK_DELAY)
                        continue
                    
                    return is_typing
                
                return False
                
            except Exception as e:
                logger.error(f"❌ Erreur check typing: {e}")
                return False
        
        return False
    
    async def fetch_conversation_history(
        self,
        match_id: str
    ) -> List[Dict]:
        """
        Charge l'historique complet de la conversation
        
        Args:
            match_id: ID du match
            
        Returns:
            Liste de messages avec profils
        """
        logger.info("📦 Chargement contexte complet...")
        
        try:
            # Charger messages avec profils
            messages = await self.supabase.select(
                'messages',
                columns='id,content,sender_id,created_at,type,profiles!messages_sender_id_fkey(first_name,is_bot)',
                filters={'match_id': match_id},
                order='created_at.asc',
                limit=self.MAX_HISTORY_MESSAGES
            )
            
            return messages if messages else []
            
        except Exception as e:
            logger.error(f"❌ Erreur fetch history: {e}")
            return []
    
    async def fetch_bot_memory(
        self,
        bot_id: str,
        user_id: str
    ) -> Optional[Dict]:
        """
        Charge la mémoire bot pour cet utilisateur
        
        Args:
            bot_id: ID du bot
            user_id: ID de l'utilisateur
            
        Returns:
            Mémoire bot ou None
        """
        try:
            result = await self.supabase.select(
                'bot_memory',
                filters={'bot_id': bot_id, 'user_id': user_id}
            )
            
            return result[0] if result and len(result) > 0 else None
            
        except Exception as e:
            logger.error(f"❌ Erreur fetch memory: {e}")
            return None
    
    async def fetch_bot_profile(
        self,
        bot_id: str
    ) -> Optional[Dict]:
        """
        Charge le profil du bot
        
        Args:
            bot_id: ID du bot
            
        Returns:
            Profil bot ou None
        """
        try:
            result = await self.supabase.select(
                'bot_profiles',
                columns='system_prompt,bot_personality,temperature',
                filters={'id': bot_id}
            )
            
            return result[0] if result and len(result) > 0 else None
            
        except Exception as e:
            logger.error(f"❌ Erreur fetch bot profile: {e}")
            return None
    
    async def prepare_context(
        self,
        match_id: str,
        bot_id: str,
        sender_id: str
    ) -> Dict:
        """
        Prépare le contexte complet pour la génération
        
        Args:
            match_id: ID du match
            bot_id: ID du bot
            sender_id: ID de l'utilisateur
            
        Returns:
            Dict avec history, memory, bot_profile
        """
        # Vérifier typing
        is_typing = await self.check_user_typing(match_id, sender_id)
        
        # Charger contexte
        history = await self.fetch_conversation_history(match_id)
        memory = await self.fetch_bot_memory(bot_id, sender_id)
        bot_profile = await self.fetch_bot_profile(bot_id)
        
        # Créer mémoire par défaut si inexistante
        if not memory:
            memory = {
                'trust_score': 0,
                'relationship_level': 'stranger',
                'conversation_tone': 'neutral',
                'preferred_topics': [],
                'topics_to_avoid': []
            }
        
        # Créer bot_profile par défaut si inexistant
        if not bot_profile:
            bot_profile = {
                'system_prompt': 'Tu es un bot conversationnel sympathique.',
                'bot_personality': 'friendly',
                'temperature': 0.8
            }
        
        # Calculer temps depuis dernier message bot
        time_since_last_bot_minutes = 999  # Default: très longtemps
        for msg in reversed(history):
            if msg.get('profiles', {}).get('is_bot'):
                last_bot_time = datetime.fromisoformat(msg['created_at'].replace('Z', '+00:00'))
                time_diff = datetime.now().astimezone() - last_bot_time
                time_since_last_bot_minutes = time_diff.total_seconds() / 60
                break
        
        logger.info(f"✅ Contexte prêt ({len(history)} msgs, trust={memory.get('trust_score', 0)})")
        
        return {
            'is_typing': is_typing,
            'history': history,
            'memory': memory,
            'bot_profile': bot_profile,
            'time_since_last_bot_minutes': time_since_last_bot_minutes
        }
