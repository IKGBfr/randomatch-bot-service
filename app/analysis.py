"""
Message Analysis - Analyse contextuelle des messages

Analyse l'urgency, complexity, emotional_tone d'un message
pour adapter le comportement du bot.
"""

import re
from typing import Dict, List


class MessageAnalyzer:
    """Analyse les messages pour déterminer le contexte"""
    
    def __init__(self):
        # Mots urgents
        self.urgent_keywords = [
            'urgent', 'vite', 'maintenant', 'immédiatement', 'besoin',
            'aide', 'sos', 'important', 'grave', 'problème'
        ]
        
        # Mots complexes (questions ouvertes, réflexion)
        self.complex_keywords = [
            'pourquoi', 'comment', 'explique', 'penses', 'opinion',
            'ressens', 'comprends', 'signifie', 'veux dire'
        ]
        
        # Émotions positives
        self.positive_emotions = [
            'haha', 'mdr', 'lol', '😂', '😊', '😄', '❤️', '💕',
            'cool', 'génial', 'super', 'top', 'trop bien'
        ]
        
        # Émotions négatives
        self.negative_emotions = [
            '😢', '😔', '😞', '💔',
            'triste', 'nul', 'chiant', 'relou', 'dommage', 'déçu'
        ]
        
        # Émotions excitées
        self.excited_emotions = [
            '!!!', '!!!!', '😍', '🤩', '🔥',
            'trop hâte', 'trop envie', 'grave', 'ouf'
        ]
    
    def analyze_message(
        self,
        message: str,
        history: List[Dict] = None,
        memory: Dict = None
    ) -> Dict:
        """
        Analyse complète d'un message
        
        Args:
            message: Le message à analyser
            history: Historique conversation (optionnel)
            memory: Mémoire bot (optionnel)
            
        Returns:
            Dict avec urgency, complexity, emotional_tone, etc.
        """
        message_lower = message.lower()
        
        # Analyse urgency
        urgency = self._analyze_urgency(message_lower)
        
        # Analyse complexity
        complexity = self._analyze_complexity(message_lower, message)
        
        # Analyse emotional tone
        emotional_tone = self._analyze_emotional_tone(message_lower, message)
        
        # Déterminer type de message
        message_type = self._determine_message_type(message_lower, message)
        
        # Recommandation délai
        recommended_delay = self._recommend_delay(urgency, complexity)
        
        # Multi-messages suggéré ?
        requires_multi = self._should_split_response(
            message, urgency, complexity, emotional_tone
        )
        
        return {
            'urgency': urgency,
            'complexity': complexity,
            'emotional_tone': emotional_tone,
            'message_type': message_type,
            'recommended_delay': recommended_delay,
            'requires_multi_messages': requires_multi,
            'message_length': len(message),
            'has_question': '?' in message
        }
    
    def _analyze_urgency(self, message: str) -> int:
        """Analyse l'urgence (1-5)"""
        urgency = 3  # Neutre par défaut
        
        # Mots urgents
        urgent_count = sum(1 for word in self.urgent_keywords if word in message)
        if urgent_count >= 2:
            urgency = 5
        elif urgent_count == 1:
            urgency = 4
        
        # Points d'exclamation multiples
        if message.count('!') >= 3:
            urgency = min(5, urgency + 1)
        
        # Majuscules (CRIER)
        caps_ratio = sum(1 for c in message if c.isupper()) / max(len(message), 1)
        if caps_ratio > 0.5:
            urgency = min(5, urgency + 1)
        
        # Question directe simple
        if message.endswith('?') and len(message.split()) < 10:
            urgency = max(3, urgency)
        
        return urgency
    
    def _analyze_complexity(self, message_lower: str, message: str) -> int:
        """Analyse la complexité (1-5)"""
        complexity = 3  # Neutre
        
        # Longueur
        word_count = len(message.split())
        if word_count > 50:
            complexity = 5
        elif word_count > 30:
            complexity = 4
        elif word_count < 10:
            complexity = 2
        
        # Mots complexes
        complex_count = sum(1 for word in self.complex_keywords if word in message_lower)
        if complex_count >= 2:
            complexity = 5
        elif complex_count == 1:
            complexity = 4
        
        # Questions multiples
        question_count = message.count('?')
        if question_count >= 3:
            complexity = 5
        elif question_count == 2:
            complexity = 4
        
        return complexity
    
    def _analyze_emotional_tone(self, message_lower: str, message: str) -> str:
        """Analyse le ton émotionnel"""
        # Compter émotions
        positive = sum(1 for word in self.positive_emotions if word in message_lower)
        negative = sum(1 for word in self.negative_emotions if word in message_lower)
        excited = sum(1 for word in self.excited_emotions if word in message_lower)
        
        # Déterminer dominant
        if excited >= 2:
            return 'excited'
        elif positive > negative:
            return 'positive'
        elif negative > positive:
            return 'sad'
        elif positive == negative == 0:
            return 'neutral'
        else:
            return 'neutral'
    
    def _determine_message_type(self, message_lower: str, message: str) -> str:
        """Détermine le type de message"""
        if '?' in message:
            return 'question'
        elif any(word in message_lower for word in ['salut', 'hello', 'coucou', 'hey']):
            return 'greeting'
        elif any(word in message_lower for word in ['merci', 'thanks', 'super']):
            return 'appreciation'
        elif len(message.split()) > 50:
            return 'story'
        else:
            return 'statement'
    
    def _recommend_delay(self, urgency: int, complexity: int) -> int:
        """Recommande un délai en secondes"""
        # Matrice urgency x complexity
        delay_matrix = {
            (5, 5): 4,  # Urgent + complexe : 4s
            (5, 4): 3,
            (5, 3): 3,
            (5, 2): 2,
            (5, 1): 2,
            (4, 5): 5,
            (4, 4): 4,
            (4, 3): 4,
            (3, 5): 7,
            (3, 4): 6,
            (3, 3): 5,
            (2, 5): 10,
            (2, 4): 9,
            (1, 5): 12,
        }
        
        return delay_matrix.get((urgency, complexity), 5)
    
    def _should_split_response(
        self,
        message: str,
        urgency: int,
        complexity: int,
        emotional_tone: str
    ) -> bool:
        """Détermine si la réponse devrait être split en plusieurs messages"""
        # Pas de split si très urgent
        if urgency >= 5:
            return False
        
        # Split si complexe
        if complexity >= 4:
            return True
        
        # Split si message long
        if len(message) > 200:
            return True
        
        # Split si excité (pour paraître naturel)
        if emotional_tone == 'excited':
            return True
        
        return False


# Instance globale
message_analyzer = MessageAnalyzer()
