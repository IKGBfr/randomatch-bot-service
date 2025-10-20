"""
Gestion du contexte éphémère dans Redis pour grouping intelligent
"""

import json
from datetime import datetime
from typing import Optional, Dict, List
import redis.asyncio as redis


class RedisContextManager:
    """Gère le contexte des conversations dans Redis"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.CONTEXT_TTL = 20  # Secondes (DOIT être > GROUPING_DELAY)
        
    def _context_key(self, match_id: str) -> str:
        """Génère la clé Redis pour le contexte"""
        return f"context:{match_id}"
    
    async def get_context(self, match_id: str) -> Optional[Dict]:
        """Récupère le contexte d'une conversation"""
        key = self._context_key(match_id)
        data = await self.redis.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    async def set_context(self, match_id: str, context: Dict):
        """Enregistre le contexte avec TTL"""
        key = self._context_key(match_id)
        await self.redis.setex(
            key,
            self.CONTEXT_TTL,
            json.dumps(context)
        )
    
    async def delete_context(self, match_id: str):
        """Supprime le contexte"""
        key = self._context_key(match_id)
        await self.redis.delete(key)
    
    async def init_context(self, match_id: str, message: Dict) -> Dict:
        """Initialise un nouveau contexte"""
        context = {
            'last_message_at': datetime.now().isoformat(),
            'rapid_count': 1,
            'messages': [message],
            'timer_started': False
        }
        await self.set_context(match_id, context)
        return context
    
    async def update_context(self, match_id: str, message: Dict) -> Dict:
        """Met à jour un contexte existant"""
        context = await self.get_context(match_id)
        
        if context:
            context['last_message_at'] = datetime.now().isoformat()
            context['rapid_count'] += 1
            context['messages'].append(message)
            await self.set_context(match_id, context)
        
        return context
