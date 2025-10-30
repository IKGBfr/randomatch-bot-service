"""
Vérification de la disponibilité des bots selon leurs horaires configurés.

Ce module gère :
- Vérification si un bot est disponible selon l'heure actuelle
- Calcul du délai jusqu'à la prochaine disponibilité
- Gestion timezone Europe/Paris
"""

import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Tuple

from app.config import Config
from app.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)

# Timezone Europe/Paris (utilisé partout dans RandoMatch)
PARIS_TZ = ZoneInfo("Europe/Paris")


class AvailabilityChecker:
    """Vérifie la disponibilité des bots selon leurs horaires configurés."""
    
    def __init__(self):
        self.supabase = SupabaseClient()
        self._bot_schedules_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = timedelta(hours=1)  # Recharger toutes les heures
    
    async def connect(self):
        """Initialise la connexion Supabase."""
        await self.supabase.connect()
    
    async def close(self):
        """Ferme la connexion Supabase."""
        await self.supabase.close()
    
    async def _load_bot_schedule(self, bot_id: str) -> Dict:
        """
        Charge les horaires d'un bot depuis la DB.
        
        Returns:
            dict: {
                'weekday_start': time(7, 30),
                'weekday_end': time(23, 0),
                'weekend_start': time(8, 0),
                'weekend_end': time(23, 30),
                'is_active': True
            }
        """
        # Vérifier cache
        now = datetime.now(PARIS_TZ)
        if (self._cache_timestamp and 
            now - self._cache_timestamp < self._cache_ttl and
            bot_id in self._bot_schedules_cache):
            return self._bot_schedules_cache[bot_id]
        
        # Charger depuis DB
        query = """
            SELECT 
                weekday_start_time,
                weekday_end_time,
                weekend_start_time,
                weekend_end_time,
                is_active
            FROM bot_profiles
            WHERE id = $1
        """
        
        result = await self.supabase.fetch_one(query, bot_id)
        
        if not result:
            logger.warning(f"Bot {bot_id} not found in bot_profiles")
            return None
        
        # Convertir en dict
        schedule = {
            'weekday_start': result['weekday_start_time'],
            'weekday_end': result['weekday_end_time'],
            'weekend_start': result['weekend_start_time'],
            'weekend_end': result['weekend_end_time'],
            'is_active': result['is_active']
        }
        
        # Mettre en cache
        self._bot_schedules_cache[bot_id] = schedule
        self._cache_timestamp = now
        
        logger.debug(f"Loaded schedule for bot {bot_id}: {schedule}")
        
        return schedule
    
    def _is_weekend(self, dt: datetime) -> bool:
        """Vérifie si une date est un weekend (samedi=5, dimanche=6)."""
        return dt.weekday() in [5, 6]
    
    def _time_in_range(self, current: time, start: time, end: time) -> bool:
        """
        Vérifie si l'heure actuelle est dans la plage [start, end].
        
        Gère le cas où end est après minuit (ex: 23:30 à 00:30).
        """
        if start <= end:
            # Cas normal: 07:30 - 23:00
            return start <= current <= end
        else:
            # Cas qui traverse minuit: 23:00 - 02:00
            return current >= start or current <= end
    
    async def is_bot_available(self, bot_id: str) -> Tuple[bool, Optional[str]]:
        """
        Vérifie si un bot est disponible pour répondre maintenant.
        
        Args:
            bot_id: UUID du bot
            
        Returns:
            tuple: (is_available: bool, reason: Optional[str])
            
        Examples:
            >>> checker = AvailabilityChecker()
            >>> is_available, reason = await checker.is_bot_available(bot_id)
            >>> if not is_available:
            >>>     logger.info(f"Bot indisponible: {reason}")
        """
        # Charger horaires du bot
        schedule = await self._load_bot_schedule(bot_id)
        
        if not schedule:
            return False, "Bot schedule not found"
        
        # Vérifier si bot actif
        if not schedule['is_active']:
            return False, "Bot is inactive"
        
        # Si aucun horaire configuré → disponible 24/7
        if not schedule['weekday_start']:
            logger.debug(f"Bot {bot_id} has no schedule restrictions (24/7)")
            return True, None
        
        # Heure actuelle à Paris
        now = datetime.now(PARIS_TZ)
        current_time = now.time()
        is_weekend = self._is_weekend(now)
        
        # Sélectionner les horaires selon jour
        if is_weekend:
            start_time = schedule['weekend_start'] or schedule['weekday_start']
            end_time = schedule['weekend_end'] or schedule['weekday_end']
            day_type = "weekend"
        else:
            start_time = schedule['weekday_start']
            end_time = schedule['weekday_end']
            day_type = "weekday"
        
        # Vérifier si dans la plage
        is_available = self._time_in_range(current_time, start_time, end_time)
        
        if is_available:
            logger.debug(
                f"Bot {bot_id} available ({day_type} {current_time.strftime('%H:%M')} "
                f"in range {start_time}-{end_time})"
            )
            return True, None
        else:
            reason = (
                f"Bot sleeping ({day_type} {current_time.strftime('%H:%M')} "
                f"outside range {start_time}-{end_time})"
            )
            logger.info(f"Bot {bot_id} unavailable: {reason}")
            return False, reason
    
    async def get_next_available_time(self, bot_id: str) -> Optional[datetime]:
        """
        Calcule le prochain moment où le bot sera disponible.
        
        Args:
            bot_id: UUID du bot
            
        Returns:
            datetime: Prochain moment disponible (timezone Paris), ou None si déjà disponible
            
        Examples:
            >>> next_time = await checker.get_next_available_time(bot_id)
            >>> if next_time:
            >>>     logger.info(f"Bot disponible à {next_time.strftime('%H:%M')}")
        """
        is_available, _ = await self.is_bot_available(bot_id)
        
        if is_available:
            return None  # Déjà disponible
        
        # Charger horaires
        schedule = await self._load_bot_schedule(bot_id)
        if not schedule or not schedule['weekday_start']:
            return None  # Pas de restrictions
        
        # Heure actuelle à Paris
        now = datetime.now(PARIS_TZ)
        current_time = now.time()
        is_weekend = self._is_weekend(now)
        
        # Déterminer la prochaine heure de début
        if is_weekend:
            next_start = schedule['weekend_start'] or schedule['weekday_start']
        else:
            next_start = schedule['weekday_start']
        
        # Créer datetime pour le prochain réveil
        next_available = datetime.combine(now.date(), next_start, tzinfo=PARIS_TZ)
        
        # Si l'heure de début est déjà passée aujourd'hui, prendre demain
        if current_time >= next_start:
            next_available += timedelta(days=1)
            
            # Si demain est un jour différent (semaine/weekend), ajuster
            tomorrow_is_weekend = self._is_weekend(next_available)
            if tomorrow_is_weekend != is_weekend:
                if tomorrow_is_weekend:
                    next_start = schedule['weekend_start'] or schedule['weekday_start']
                else:
                    next_start = schedule['weekday_start']
                
                next_available = datetime.combine(
                    next_available.date(),
                    next_start,
                    tzinfo=PARIS_TZ
                )
        
        logger.debug(f"Next available time for bot {bot_id}: {next_available}")
        
        return next_available
    
    async def calculate_delay_until_available(self, bot_id: str) -> Optional[int]:
        """
        Calcule le délai en secondes jusqu'à la prochaine disponibilité du bot.
        
        Args:
            bot_id: UUID du bot
            
        Returns:
            int: Nombre de secondes à attendre, ou None si déjà disponible
            
        Examples:
            >>> delay = await checker.calculate_delay_until_available(bot_id)
            >>> if delay:
            >>>     logger.info(f"Bot sera disponible dans {delay/3600:.1f}h")
        """
        next_time = await self.get_next_available_time(bot_id)
        
        if not next_time:
            return None  # Déjà disponible ou pas de restrictions
        
        now = datetime.now(PARIS_TZ)
        delay_seconds = int((next_time - now).total_seconds())
        
        logger.info(
            f"Bot {bot_id} sera disponible dans {delay_seconds}s "
            f"({delay_seconds/3600:.1f}h) à {next_time.strftime('%Y-%m-%d %H:%M')}"
        )
        
        return delay_seconds


# Instance globale
_availability_checker = None


async def get_availability_checker() -> AvailabilityChecker:
    """Retourne l'instance globale du checker (singleton)."""
    global _availability_checker
    
    if _availability_checker is None:
        _availability_checker = AvailabilityChecker()
        await _availability_checker.connect()
    
    return _availability_checker
