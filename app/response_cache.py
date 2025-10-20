"""
Response Cache - Évite génération de réponses identiques/similaires

Utilise Redis pour stocker:
1. Intent de réponse (flag "generating")
2. Réponses récentes (pour deduplication)
3. TTL 60s (expire automatiquement)
"""

import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict
import redis.asyncio as redis
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class ResponseCache:
    """Cache Redis pour éviter doublons de réponses"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.CACHE_TTL = 60  # Secondes - expire auto
        self.SIMILARITY_THRESHOLD = 0.8  # 80% similarité = doublon
    
    def _make_key(self, match_id: str, key_type: str) -> str:
        """Génère clé Redis"""
        return f"response:{key_type}:{match_id}"
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcule similarité entre 2 textes (0.0 à 1.0)"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    async def is_generating(self, match_id: str) -> bool:
        """Check si une génération est déjà en cours"""
        key = self._make_key(match_id, "generating")
        exists = await self.redis.exists(key)
        
        if exists:
            data = await self.redis.get(key)
            if data:
                generating_data = json.loads(data)
                logger.info(f"⚠️ Génération déjà en cours depuis {generating_data.get('started_at')}")
                return True
        
        return False
    
    async def mark_generating(self, match_id: str, user_message: str):
        """Marque qu'une génération démarre"""
        key = self._make_key(match_id, "generating")
        
        data = {
            'started_at': datetime.now().isoformat(),
            'user_message': user_message,
            'status': 'generating'
        }
        
        await self.redis.setex(
            key,
            self.CACHE_TTL,
            json.dumps(data)
        )
        
        logger.info(f"🔒 Génération marquée en cours (TTL {self.CACHE_TTL}s)")
    
    async def clear_generating(self, match_id: str):
        """Clear le flag de génération"""
        key = self._make_key(match_id, "generating")
        await self.redis.delete(key)
        logger.info("🔓 Flag génération cleared")
    
    async def store_response(self, match_id: str, bot_response: str, user_message: str):
        """Stocke une réponse dans le cache"""
        key = self._make_key(match_id, "recent")
        
        # Récupérer réponses existantes
        existing = await self.redis.get(key)
        
        if existing:
            responses = json.loads(existing)
        else:
            responses = []
        
        # Ajouter nouvelle réponse
        responses.append({
            'response': bot_response,
            'user_message': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Garder seulement les 5 dernières
        responses = responses[-5:]
        
        # Stocker avec TTL
        await self.redis.setex(
            key,
            self.CACHE_TTL,
            json.dumps(responses)
        )
        
        logger.info(f"💾 Réponse stockée en cache (total: {len(responses)})")
    
    async def find_similar_response(
        self, 
        match_id: str, 
        user_message: str
    ) -> Optional[str]:
        """
        Cherche une réponse similaire récente
        
        Returns:
            str si doublon trouvé, None sinon
        """
        key = self._make_key(match_id, "recent")
        existing = await self.redis.get(key)
        
        if not existing:
            return None
        
        responses = json.loads(existing)
        
        # Check chaque réponse récente
        for resp_data in responses:
            # Comparer user_message pour voir si même contexte
            user_similarity = self._calculate_similarity(
                user_message,
                resp_data['user_message']
            )
            
            if user_similarity > 0.7:  # Même question
                logger.warning(f"⚠️ Question similaire trouvée!")
                logger.warning(f"   User msg: {user_message[:50]}")
                logger.warning(f"   Cached: {resp_data['user_message'][:50]}")
                logger.warning(f"   Similarity: {user_similarity:.2%}")
                logger.warning(f"   → Réponse déjà envoyée: {resp_data['response'][:50]}")
                
                return resp_data['response']
        
        return None
    
    async def is_duplicate_response(
        self,
        match_id: str,
        new_response: str
    ) -> bool:
        """
        Check si la réponse générée est trop similaire aux récentes
        
        Returns:
            True si doublon, False sinon
        """
        key = self._make_key(match_id, "recent")
        existing = await self.redis.get(key)
        
        if not existing:
            return False
        
        responses = json.loads(existing)
        
        # Comparer avec chaque réponse récente
        for resp_data in responses:
            similarity = self._calculate_similarity(
                new_response,
                resp_data['response']
            )
            
            if similarity >= self.SIMILARITY_THRESHOLD:
                logger.warning(f"❌ DOUBLON DÉTECTÉ!")
                logger.warning(f"   Nouvelle: {new_response[:50]}")
                logger.warning(f"   Existante: {resp_data['response'][:50]}")
                logger.warning(f"   Similarité: {similarity:.2%}")
                logger.warning(f"   → SKIP cette réponse")
                
                return True
        
        return False
    
    async def get_recent_responses(self, match_id: str) -> List[Dict]:
        """Récupère toutes les réponses récentes (debug)"""
        key = self._make_key(match_id, "recent")
        existing = await self.redis.get(key)
        
        if existing:
            return json.loads(existing)
        
        return []
