"""
Timing Engine - Calculs de délais naturels et humains

Gère les délais de réflexion et de frappe pour simuler
un comportement humain naturel.
"""

import random
from typing import Dict
from datetime import datetime, time


class TimingEngine:
    """Calcule les délais adaptatifs pour comportement naturel"""
    
    def __init__(self):
        # Configuration par défaut
        self.CHARS_PER_SECOND = 3.5  # Vitesse frappe humaine
        self.MIN_THINKING_DELAY = 2  # Secondes
        self.MAX_THINKING_DELAY = 15  # Secondes
    
    def calculate_thinking_delay(
        self,
        analysis: Dict,
        message_length: int,
        time_since_last_bot: float = 0,
        current_time: datetime = None
    ) -> float:
        """
        Calcule le délai de réflexion avant de répondre
        
        Args:
            analysis: Dict avec urgency, complexity, etc.
            message_length: Longueur du message user
            time_since_last_bot: Temps depuis dernier message bot (secondes)
            current_time: Heure actuelle (pour timing horaire)
            
        Returns:
            Délai en secondes (float)
        """
        urgency = analysis.get('urgency', 3)  # 1-5
        complexity = analysis.get('complexity', 3)  # 1-5
        
        # Base selon urgence
        urgency_delays = {
            5: 2,   # Très urgent : 2s
            4: 3,   # Urgent : 3s
            3: 5,   # Normal : 5s
            2: 8,   # Pas urgent : 8s
            1: 12   # Très posé : 12s
        }
        base_delay = urgency_delays.get(urgency, 5)
        
        # 🆕 PHASE 4: Ajustement selon heure de la journée
        if current_time:
            base_delay = self._adjust_delay_for_time_of_day(base_delay, current_time)
        
        # Ajustement selon complexité
        if complexity >= 4:
            base_delay += 3  # Questions complexes : +3s
        elif complexity <= 2:
            base_delay -= 1  # Questions simples : -1s
        
        # Ajustement selon longueur message user
        if message_length > 200:
            base_delay += 2  # Long message : +2s réflexion
        elif message_length > 500:
            base_delay += 4  # Très long : +4s
        
        # Si bot vient de répondre récemment
        if time_since_last_bot < 30:  # < 30 secondes
            base_delay = max(2, base_delay - 2)  # Réponse plus rapide
        
        # Variabilité naturelle (-1 à +2 secondes)
        variance = random.uniform(-1, 2)
        final_delay = max(self.MIN_THINKING_DELAY, base_delay + variance)
        
        # Cap max
        final_delay = min(final_delay, self.MAX_THINKING_DELAY)
        
        return round(final_delay, 2)
    
    def calculate_typing_time(self, text: str) -> float:
        """
        Calcule le temps de frappe réaliste pour un texte
        
        Args:
            text: Le texte à "taper"
            
        Returns:
            Temps en secondes (float)
        """
        # Base : longueur / vitesse
        base_time = len(text) / self.CHARS_PER_SECOND
        
        # Pauses sur ponctuation (mimique réflexion)
        punctuation_count = (
            text.count('.') + 
            text.count(',') + 
            text.count('!') + 
            text.count('?')
        )
        pause_time = punctuation_count * 0.3  # 0.3s par ponctuation
        
        # Pauses sur emojis (prend du temps à chercher/choisir)
        emoji_count = sum(1 for c in text if ord(c) > 127)
        emoji_time = emoji_count * 0.5  # 0.5s par emoji
        
        # Variabilité naturelle
        variance = random.uniform(-0.5, 1.0)
        
        final_time = max(1, base_time + pause_time + emoji_time + variance)
        
        return round(final_time, 2)
    
    def calculate_pause_between_messages(self, previous_length: int) -> float:
        """
        Calcule la pause entre plusieurs messages consécutifs
        
        Args:
            previous_length: Longueur du message précédent
            
        Returns:
            Pause en secondes (float)
        """
        # Base : 1.5-3 secondes
        base_pause = random.uniform(1.5, 3)
        
        # Si message précédent long, pause plus courte
        # (momentum de la conversation)
        if previous_length > 100:
            base_pause *= 0.7
        
        return round(base_pause, 2)
    
    def should_split_message(self, text: str) -> bool:
        """
        Détermine si un message devrait être divisé en plusieurs
        
        Args:
            text: Le texte à analyser
            
        Returns:
            True si devrait être divisé
        """
        # Critères pour split
        has_multiple_thoughts = text.count('.') >= 2 or text.count('!') >= 2
        is_long = len(text) > 150
        has_question_and_statement = '?' in text and '.' in text
        
        return has_multiple_thoughts and (is_long or has_question_and_statement)
    
    def _adjust_delay_for_time_of_day(self, base_delay: float, current_time: datetime) -> float:
        """
        Ajuste le délai selon l'heure (Phase 4: Disponibilité Variable)
        
        Plages horaires :
        - 7h-9h : Réveil, peu actif → +50%
        - 9h-17h : Travail, indispo → +200%
        - 17h-20h : Retour travail → +30%
        - 20h-23h : Très actif → base
        - 23h-7h : Sommeil → +500%
        """
        hour = current_time.hour
        is_weekend = current_time.weekday() >= 5  # 5=samedi, 6=dimanche
        
        # Weekend : plus flexible
        if is_weekend:
            if 9 <= hour < 12:  # Matin relax
                return base_delay * 1.2
            elif 12 <= hour < 20:  # Journée active
                return base_delay * 0.9
            elif 20 <= hour < 23:  # Soirée
                return base_delay
            else:  # Nuit
                return base_delay * 3
        
        # Semaine : horaires travail
        if 7 <= hour < 9:  # Réveil
            return base_delay * 1.5
        elif 9 <= hour < 12 or 14 <= hour < 17:  # Travail
            return base_delay * 3  # Très indispo
        elif 12 <= hour < 14:  # Pause déj
            return base_delay * 1.3
        elif 17 <= hour < 20:  # Retour travail
            return base_delay * 1.3
        elif 20 <= hour < 23:  # Soirée = peak
            return base_delay  # Normal
        else:  # 23h-7h = Nuit
            return base_delay * 5  # Dort
    
    def is_active_hours(self, current_time: datetime = None) -> bool:
        """
        Vérifie si c'est une heure active pour le bot
        
        Returns:
            True si heure active, False si indispo
        """
        if not current_time:
            current_time = datetime.now()
        
        hour = current_time.hour
        is_weekend = current_time.weekday() >= 5
        
        # Nuit : toujours inactif
        if hour < 7 or hour >= 23:
            return False
        
        # Weekend : actif 9h-23h
        if is_weekend:
            return 9 <= hour < 23
        
        # Semaine : évite 9h-17h (travail)
        return not (9 <= hour < 17)
    
    def estimate_total_response_time(
        self,
        thinking_delay: float,
        typing_times: list,
        pauses: list
    ) -> float:
        """
        Estime le temps total de réponse
        
        Args:
            thinking_delay: Temps de réflexion
            typing_times: Liste des temps de frappe
            pauses: Liste des pauses entre messages
            
        Returns:
            Temps total en secondes
        """
        total = thinking_delay + sum(typing_times) + sum(pauses)
        return round(total, 2)


# Instance globale
timing_engine = TimingEngine()
