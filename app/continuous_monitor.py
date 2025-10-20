"""
Continuous Monitor - Surveille les nouveaux messages pendant tout le traitement
"""
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ContinuousMonitor:
    """
    Monitore en continu les nouveaux messages pendant un traitement.
    
    Principe:
    - Démarre un monitoring en background dès le début du traitement
    - Check régulièrement si de nouveaux messages sont arrivés
    - Si nouveaux messages détectés, flag pour annuler le traitement en cours
    
    Cela empêche d'envoyer une réponse obsolète alors que l'user a envoyé
    d'autres messages entre temps.
    """
    
    def __init__(self, supabase_client):
        """
        Args:
            supabase_client: Client Supabase avec méthode fetch_one
        """
        self.supabase = supabase_client
        self.should_stop = False
        self.new_messages_detected = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start(
        self,
        match_id: str,
        base_message_count: int,
        check_interval: float = 2.0
    ):
        """
        Démarre le monitoring continu en background.
        
        Args:
            match_id: ID du match à surveiller
            base_message_count: Nombre de messages au début du traitement
            check_interval: Intervalle entre chaque check (secondes)
        """
        self.should_stop = False
        self.new_messages_detected = False
        
        logger.info(
            f"👁️  Monitoring continu DÉMARRÉ "
            f"(base: {base_message_count} messages)"
        )
        
        async def monitor_loop():
            """Loop qui tourne en background"""
            while not self.should_stop:
                try:
                    # Compte les messages actuels dans ce match
                    query = """
                        SELECT COUNT(*) as count
                        FROM messages
                        WHERE match_id = $1
                        AND is_deleted = false
                    """
                    result = await self.supabase.fetch_one(query, match_id)
                    current_count = result['count']
                    
                    # Nouveaux messages détectés ?
                    if current_count > base_message_count:
                        new_count = current_count - base_message_count
                        logger.warning(
                            f"⚠️  NOUVEAUX MESSAGES DÉTECTÉS: +{new_count} "
                            f"({base_message_count} → {current_count})"
                        )
                        self.new_messages_detected = True
                        # On arrête le monitoring, le flag est set
                        break
                    
                    # Attendre avant le prochain check
                    await asyncio.sleep(check_interval)
                    
                except Exception as e:
                    logger.error(f"❌ Erreur monitoring: {e}")
                    # Continue quand même après une pause
                    await asyncio.sleep(check_interval)
        
        # Lance le monitoring en background task
        self._monitor_task = asyncio.create_task(monitor_loop())
    
    async def stop(self) -> bool:
        """
        Arrête le monitoring et retourne le résultat.
        
        Returns:
            True si nouveaux messages ont été détectés
            False sinon
        """
        self.should_stop = True
        
        # Attend que la task se termine proprement
        if self._monitor_task:
            try:
                await asyncio.wait_for(self._monitor_task, timeout=1.0)
            except asyncio.TimeoutError:
                # Force cancel si trop long
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
        
        status = "❌ nouveaux messages" if self.new_messages_detected else "✅ pas de nouveaux messages"
        logger.info(f"⏹️  Monitoring ARRÊTÉ ({status})")
        
        return self.new_messages_detected
    
    def has_new_messages(self) -> bool:
        """
        Vérifie immédiatement si de nouveaux messages ont été détectés.
        
        Returns:
            True si nouveaux messages détectés
            False sinon
        """
        return self.new_messages_detected
    
    async def check_now(self, match_id: str, base_count: int) -> bool:
        """
        Effectue un check immédiat (synchrone) sans monitoring continu.
        Utile pour une vérification ponctuelle.
        
        Args:
            match_id: ID du match
            base_count: Nombre de messages de référence
            
        Returns:
            True si nouveaux messages trouvés
            False sinon
        """
        try:
            query = """
                SELECT COUNT(*) as count
                FROM messages
                WHERE match_id = $1
                AND is_deleted = false
            """
            result = await self.supabase.fetch_one(query, match_id)
            current_count = result['count']
            
            if current_count > base_count:
                logger.warning(
                    f"⚠️  Check immédiat: +{current_count - base_count} nouveaux messages"
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur check immédiat: {e}")
            return False
