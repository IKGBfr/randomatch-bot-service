"""
Relance Builder - Génère des messages de relance naturels après abandon

Détecte conversations où user a envoyé message sans réponse depuis 2-4h
et génère une relance authentique avec excuse + question d'accroche.
"""

import logging
import random
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RelanceBuilder:
    """Génère des messages de relance naturels"""
    
    def __init__(self):
        # Templates d'excuses VAGUES (jamais d'activité datée précise)
        self.EXCUSES = [
            "Désolé j'étais occupée",
            "Sorry j'ai été débordée",
            "Excuse-moi j'ai oublié de répondre",
            "Désolée je viens juste de voir ton message",
            "Sorry j'ai pas eu le temps de répondre",
            "Excuse-moi j'ai complètement zappé",
            "Désolée j'ai été pas mal prise",
            "Sorry j'ai pas fait gaffe à mon tel",
            "Excuse-moi j'étais un peu dans ma bulle",
            "Désolée j'ai mis du temps à répondre",
            "Sorry je réponds tard",
            "Excuse-moi pour le délai"
        ]
        
        # Questions d'accroche par thème
        self.FOLLOW_UPS = {
            'hiking': [
                "Alors, c'est quand ta prochaine rando ?",
                "Tu as des sorties de prévues ce weekend ?",
                "Tu connais des spots sympas dans le coin ?",
                "Tu fais quoi comme type de randos d'habitude ?",
                "T'es plutôt montagne ou forêt ?"
            ],
            'general': [
                "Comment ça va sinon ?",
                "Quoi de neuf de ton côté ?",
                "Tu fais quoi de beau en ce moment ?",
                "Comment s'est passée ta semaine ?",
                "Des projets sympa ?"
            ],
            'weekend': [
                "Tu fais quoi ce weekend ?",
                "Des plans pour le weekend ?",
                "Tu as prévu des trucs sympas ?",
                "Tu sors ce weekend ou pas trop ?",
                "Weekend tranquille ou actif ?"
            ],
            'interests': [
                "Tu pratiques d'autres sports à côté de la rando ?",
                "T'as d'autres passions outdoor ?",
                "Tu fais quoi quand tu randos pas ?",
                "T'es plutôt sportive ou relax ?",
                "C'est quoi tes autres hobbies ?"
            ]
        }
    
    def build_relance_message(
        self,
        bot_profile: Dict,
        user_profile: Dict,
        hours_since_last_message: float
    ) -> str:
        """
        Génère un message de relance naturel adapté au contexte.
        
        Args:
            bot_profile: Profil du bot
            user_profile: Profil de l'utilisateur
            hours_since_last_message: Heures écoulées depuis dernier message user
            
        Returns:
            str: Message de relance complet
        """
        try:
            # Choisir excuse vague et générique
            excuse = random.choice(self.EXCUSES)
            
            # Choisir question d'accroche
            follow_up_theme = self._choose_follow_up_theme(user_profile)
            follow_up = random.choice(self.FOLLOW_UPS[follow_up_theme])
            
            # Assembler avec emoji naturel
            emojis = ['😅', '😊', '🙃']
            emoji = random.choice(emojis)
            
            # Format : Excuse + emoji + question
            message = f"{excuse} {emoji} {follow_up}"
            
            logger.info(f"✅ Relance générée: {message}")
            
            return message
            
        except Exception as e:
            logger.error(f"❌ Erreur build_relance_message: {e}")
            # Fallback simple et vague
            return "Hey ! Désolé pour le délai 😅 Comment ça va ?"

    
    def _choose_follow_up_theme(self, user_profile: Dict) -> str:
        """
        Choisit le thème de la question d'accroche selon profil user.
        
        Args:
            user_profile: Profil utilisateur avec hiking_level, interests, etc.
            
        Returns:
            str: Thème ('hiking', 'general', 'weekend', 'interests')
        """
        # Si user a niveau rando avancé → question hiking
        hiking_level = user_profile.get('hiking_level', '').lower()
        if hiking_level in ['advanced', 'expert']:
            return 'hiking' if random.random() < 0.7 else 'interests'
        
        # Si proche du weekend (jeudi/vendredi)
        day = datetime.now().weekday()
        if day in [3, 4]:  # Jeudi, vendredi
            return 'weekend' if random.random() < 0.6 else 'hiking'
        
        # Si user a beaucoup d'intérêts listés
        interests = user_profile.get('interests', [])
        if len(interests) >= 3:
            return 'interests' if random.random() < 0.5 else 'hiking'
        
        # Défaut : question rando (on est sur RandoMatch!)
        weights = {
            'hiking': 0.5,
            'general': 0.2,
            'weekend': 0.2,
            'interests': 0.1
        }
        
        return random.choices(
            list(weights.keys()),
            weights=list(weights.values())
        )[0]
    
    def should_send_relance(
        self,
        hours_since_last: float,
        last_relance_hours_ago: Optional[float]
    ) -> bool:
        """
        Détermine si une relance doit être envoyée.
        
        Args:
            hours_since_last: Heures depuis dernier message user
            last_relance_hours_ago: Heures depuis dernière relance (None si jamais)
            
        Returns:
            bool: True si relance nécessaire
        """
        # Délai minimum : 2h après message user
        if hours_since_last < 2:
            return False
        
        # Délai maximum : 48h (après = conversation vraiment morte)
        if hours_since_last > 48:
            return False
        
        # Si déjà relancé récemment : attendre 24h minimum
        if last_relance_hours_ago is not None and last_relance_hours_ago < 24:
            logger.info(f"Dernière relance il y a {last_relance_hours_ago:.1f}h, trop récent")
            return False
        
        # Probabilité croissante avec le temps
        if 2 <= hours_since_last < 4:
            # 2-4h : 30% chance
            return random.random() < 0.3
        elif 4 <= hours_since_last < 8:
            # 4-8h : 60% chance
            return random.random() < 0.6
        elif 8 <= hours_since_last < 24:
            # 8-24h : 80% chance
            return random.random() < 0.8
        else:
            # >24h : 100% chance
            return True
