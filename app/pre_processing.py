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
        self.MAX_HISTORY_MESSAGES = 200  # Grok 4 Fast: 2M tokens context window
        self.TYPING_CHECK_DELAY = 3  # Secondes - attendre plus longtemps
        self.MAX_TYPING_CHECKS = 3  # Vérifier 3 fois maximum
    
    async def check_user_typing(
        self,
        match_id: str,
        user_id: str,
        max_retries: int = None
    ) -> bool:
        """
        Vérifie si l'user est en train de taper
        Plus strict : vérifie aussi la fraîcheur du typing
        
        Args:
            match_id: ID du match
            user_id: ID de l'utilisateur
            max_retries: Nombre de re-vérifications (default: MAX_TYPING_CHECKS)
            
        Returns:
            True si user tape encore, False sinon
        """
        if max_retries is None:
            max_retries = self.MAX_TYPING_CHECKS
        
        for attempt in range(max_retries + 1):
            try:
                # Récupérer événement typing avec SQL direct pour fraîcheur
                query = """
                    SELECT is_typing, updated_at
                    FROM typing_events
                    WHERE match_id = $1 AND user_id = $2
                    LIMIT 1
                """
                result = await self.supabase.fetch_one(query, match_id, user_id)
                
                if result:
                    is_typing = result['is_typing']
                    updated_at = result['updated_at']
                    
                    # Vérifier que le typing est récent (< 5 secondes)
                    if is_typing and updated_at:
                        from datetime import timezone, timedelta
                        now = datetime.now(timezone.utc)
                        
                        # Convertir updated_at si nécessaire
                        if isinstance(updated_at, str):
                            typing_time = datetime.fromisoformat(str(updated_at).replace('Z', '+00:00'))
                        else:
                            typing_time = updated_at.replace(tzinfo=timezone.utc) if updated_at.tzinfo is None else updated_at
                        
                        # Si typing récent (< 5s), c'est actif
                        if (now - typing_time) < timedelta(seconds=5):
                            if attempt < max_retries:
                                logger.info(f"   ⌛ User tape ACTIVEMENT (updated {(now - typing_time).seconds}s ago, check {attempt+1}/{max_retries+1})")
                                await asyncio.sleep(self.TYPING_CHECK_DELAY)
                                continue
                            else:
                                logger.info(f"   ⚠️ User toujours en train de taper après {max_retries} checks")
                                return True
                        else:
                            # Typing trop vieux, considéré comme inactif
                            logger.info(f"   ℹ️ Typing event trop ancien ({(now - typing_time).seconds}s), considéré inactif")
                            return False
                    
                    # is_typing = False
                    return False
                
                # Pas de typing event trouvé
                return False
                
            except Exception as e:
                logger.error(f"❌ Erreur check typing: {e}")
                return False
        
        # Après toutes les vérifications
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
            # Utiliser SQL brut avec JOIN pour asyncpg
            query = """
                SELECT 
                    m.id,
                    m.content,
                    m.sender_id,
                    m.created_at,
                    m.type,
                    p.first_name,
                    p.is_bot
                FROM messages m
                LEFT JOIN profiles p ON m.sender_id = p.id
                WHERE m.match_id = $1
                ORDER BY m.created_at ASC
                LIMIT $2
            """
            
            messages = await self.supabase.fetch(query, match_id, self.MAX_HISTORY_MESSAGES)
            
            # Transformer en format attendu
            result = []
            for msg in messages:
                result.append({
                    'id': str(msg['id']),
                    'content': msg['content'],
                    'sender_id': str(msg['sender_id']),
                    'created_at': msg['created_at'],  # Déjà un datetime object
                    'type': msg['type'],
                    'profiles': {
                        'first_name': msg['first_name'],
                        'is_bot': msg['is_bot']
                    }
                })
            
            return result
            
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
            
            if result and len(result) > 0:
                profile = result[0]
                # Convertir Decimal en float
                if 'temperature' in profile and profile['temperature'] is not None:
                    from decimal import Decimal
                    if isinstance(profile['temperature'], Decimal):
                        profile['temperature'] = float(profile['temperature'])
                return profile
            
            return None
            
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
                last_bot_time = msg['created_at']
                # Si c'est un string ISO, convertir en datetime
                if isinstance(last_bot_time, str):
                    last_bot_time = datetime.fromisoformat(last_bot_time.replace('Z', '+00:00'))
                # Si déjà datetime, utiliser directement
                elif not isinstance(last_bot_time, datetime):
                    continue
                    
                # S'assurer que last_bot_time est timezone-aware
                if last_bot_time.tzinfo is None:
                    from datetime import timezone
                    last_bot_time = last_bot_time.replace(tzinfo=timezone.utc)
                    
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
