"""
Conversation Lock - Empêche traitements simultanés d'un même match
"""
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ConversationLock:
    """
    Lock Redis pour garantir qu'un seul traitement par match à la fois.
    
    Principe:
    - Avant de traiter un message, on acquiert un lock sur le match_id
    - Si le lock existe déjà, le message est repoussé dans la queue
    - Le lock est automatiquement libéré après traitement (ou après TTL)
    
    Cela empêche les doubles réponses causées par des messages reçus
    pendant qu'une génération est en cours.
    """
    
    def __init__(self, redis_client):
        """
        Args:
            redis_client: Client Redis (redis.asyncio.Redis)
        """
        self.redis = redis_client
        self.LOCK_TTL = 180  # 3 minutes max (safety)
    
    async def acquire(self, match_id: str, timeout: int = 5) -> bool:
        """
        Tente d'acquérir le lock pour ce match.
        
        Args:
            match_id: ID du match à locker
            timeout: Timeout pour l'acquisition (unused pour l'instant)
        
        Returns:
            True si lock acquis avec succès
            False si match déjà en cours de traitement
        """
        lock_key = f"conversation_lock:{match_id}"
        lock_value = datetime.now().isoformat()
        
        # SET NX = Set if Not eXists
        # Retourne 1 si la clé n'existait pas (lock acquis)
        # Retourne 0 si la clé existait déjà (lock déjà pris)
        acquired = await self.redis.set(
            lock_key,
            lock_value,
            ex=self.LOCK_TTL,  # Expire après LOCK_TTL secondes
            nx=True  # Only set if key doesn't exist
        )
        
        if acquired:
            logger.info(f"🔒 Lock ACQUIS pour match {match_id[:8]}...")
        else:
            logger.warning(f"⏸️  Lock DÉJÀ PRIS pour match {match_id[:8]}")
        
        return bool(acquired)
    
    async def release(self, match_id: str):
        """
        Libère le lock pour ce match.
        
        Args:
            match_id: ID du match à délocker
        """
        lock_key = f"conversation_lock:{match_id}"
        deleted = await self.redis.delete(lock_key)
        
        if deleted:
            logger.info(f"🔓 Lock LIBÉRÉ pour match {match_id[:8]}")
        else:
            logger.warning(f"⚠️  Lock déjà expiré pour match {match_id[:8]}")
    
    async def extend(self, match_id: str):
        """
        Prolonge le TTL du lock (utile pour générations très longues).
        
        Args:
            match_id: ID du match
        """
        lock_key = f"conversation_lock:{match_id}"
        await self.redis.expire(lock_key, self.LOCK_TTL)
        logger.debug(f"⏰ Lock TTL prolongé pour match {match_id[:8]}")
    
    async def is_locked(self, match_id: str) -> bool:
        """
        Vérifie si le match est actuellement locké.
        
        Args:
            match_id: ID du match
            
        Returns:
            True si locké, False sinon
        """
        lock_key = f"conversation_lock:{match_id}"
        exists = await self.redis.exists(lock_key)
        return bool(exists)
    
    async def get_lock_info(self, match_id: str) -> Optional[str]:
        """
        Récupère les infos du lock (timestamp acquisition).
        
        Args:
            match_id: ID du match
            
        Returns:
            Timestamp ISO du lock, ou None si pas locké
        """
        lock_key = f"conversation_lock:{match_id}"
        value = await self.redis.get(lock_key)
        return value.decode() if value else None
