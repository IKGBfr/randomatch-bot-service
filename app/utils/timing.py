"""
Timing Engine - Calculs de délais naturels et humains

Gère les délais de réflexion et de frappe pour simuler
un comportement humain naturel.
"""

import random
from typing import Dict


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
        time_since_last_bot: float = 0
    ) -> float:
        """
        Calcule le délai de réflexion avant de répondre
        
        Args:
            analysis: Dict avec urgency, complexity, etc.
            message_length: Longueur du message user
            time_since_last_bot: Temps depuis dernier message bot (secondes)
            
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
