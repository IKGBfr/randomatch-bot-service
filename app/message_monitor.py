"""
Message Monitor - Détecte nouveaux messages pendant le traitement
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class MessageMonitor:
    """
    Surveille l'arrivée de nouveaux messages pendant le traitement
    Permet d'annuler si user continue à écrire
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.monitoring = False
        self.new_messages_detected = False
        self.last_message_count = 0
        
    async def start_monitoring(
        self, 
        match_id: str, 
        initial_message_count: int,
        check_interval: float = 0.5  # Vérifier toutes les 500ms
    ):
        """
        Démarre la surveillance des nouveaux messages
        
        Args:
            match_id: ID du match à surveiller
            initial_message_count: Nombre de messages au début du traitement
            check_interval: Intervalle de vérification en secondes
        """
        self.monitoring = True
        self.new_messages_detected = False
        self.last_message_count = initial_message_count
        
        logger.info(f"👁️  Démarrage monitoring messages (base: {initial_message_count})")
        
        while self.monitoring:
            await asyncio.sleep(check_interval)
            
            # Vérifier si nouveaux messages
            current_count = await self._get_message_count(match_id)
            
            if current_count > self.last_message_count:
                new_count = current_count - self.last_message_count
                logger.warning(f"🆕 {new_count} nouveau(x) message(s) détecté(s) !")
                self.new_messages_detected = True
                self.monitoring = False  # Arrêter monitoring
                break
    
    async def _get_message_count(self, match_id: str) -> int:
        """Compte les messages dans un match"""
        try:
            # Utiliser fetch_one car SELECT retourne un résultat
            result = await self.supabase.fetch_one(
                """
                SELECT COUNT(*) as count
                FROM messages
                WHERE match_id = $1
                """,
                match_id
            )
            
            if result:
                return result['count']
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erreur comptage messages: {e}")
            return self.last_message_count  # Garder ancien count si erreur
    
    def stop_monitoring(self):
        """Arrête la surveillance"""
        self.monitoring = False
        logger.info("⏹️  Arrêt monitoring")
    
    def has_new_messages(self) -> bool:
        """Vérifie si de nouveaux messages ont été détectés"""
        return self.new_messages_detected
    
    async def check_once(self, match_id: str, initial_count: int) -> bool:
        """
        Vérification unique (sans boucle continue)
        
        Returns:
            True si nouveaux messages détectés
        """
        current_count = await self._get_message_count(match_id)
        
        if current_count > initial_count:
            new_count = current_count - initial_count
            logger.warning(f"🆕 {new_count} nouveau(x) message(s) détecté(s) !")
            return True
        
        return False
