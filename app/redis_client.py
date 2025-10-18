"""Client Redis pour la queue de messages."""

from typing import Dict, Optional
import redis.asyncio as redis
import json
from app.config import settings


class RedisClient:
    """Client Redis singleton pour gérer la queue."""
    
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    async def get_client(cls) -> redis.Redis:
        """Retourne instance Redis client."""
        if cls._instance is None:
            cls._instance = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return cls._instance
    
    @classmethod
    async def push_message(cls, payload: Dict) -> int:
        """
        Ajoute un message à la queue.
        
        Args:
            payload: Dict avec bot_id, match_id, user_id, message, etc.
            
        Returns:
            Longueur de la queue après insertion
        """
        client = await cls.get_client()
        message_json = json.dumps(payload)
        length = await client.rpush('bot_messages', message_json)
        return length
    
    @classmethod
    async def pop_message(cls, timeout: int = 1) -> Optional[Dict]:
        """
        Récupère le prochain message de la queue (bloquant).
        
        Args:
            timeout: Secondes d'attente max
            
        Returns:
            Dict du message ou None si timeout
        """
        client = await cls.get_client()
        result = await client.blpop('bot_messages', timeout=timeout)
        
        if result:
            _, message_json = result
            return json.loads(message_json)
        return None
    
    @classmethod
    async def get_queue_length(cls) -> int:
        """Retourne le nombre de messages en attente."""
        client = await cls.get_client()
        return await client.llen('bot_messages')
    
    @classmethod
    async def clear_queue(cls):
        """Vide complètement la queue (pour debug)."""
        client = await cls.get_client()
        await client.delete('bot_messages')
    
    @classmethod
    async def close(cls):
        """Ferme la connexion Redis."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None


# Helper functions
async def push_to_queue(payload: Dict) -> int:
    """Helper pour pousser dans la queue."""
    return await RedisClient.push_message(payload)


async def pop_from_queue(timeout: int = 1) -> Optional[Dict]:
    """Helper pour récupérer de la queue."""
    return await RedisClient.pop_message(timeout)


async def get_queue_size() -> int:
    """Helper pour obtenir taille queue."""
    return await RedisClient.get_queue_length()
