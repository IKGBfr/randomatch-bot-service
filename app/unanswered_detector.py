"""
Détecteur de Messages Sans Réponse
Analyse si l'utilisateur attend une réponse du bot
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class UnansweredDetector:
    """Détecte si user attend réponse urgente"""
    
    def __init__(self):
        self.min_consecutive_for_urgent = 2  # 2+ messages = urgent
        self.max_wait_minutes = 5  # Après 5min sans réponse = problème
    
    async def needs_urgent_response(
        self,
        messages: List[Dict]
        # 🔧 SUPPRIMÉ: bot_id (on utilise is_bot à la place)
    ) -> Dict:
        """
        Analyse si bot DOIT répondre maintenant
        
        Returns:
            {
                'urgent': bool,  # Si réponse IMMÉDIATE nécessaire
                'consecutive_user_messages': int,
                'minutes_waiting': float,
                'context': str,  # USER_CONFUSED, USER_REPEATING, etc.
                'last_bot_message': str,
                'user_messages_since_bot': List[str]
            }
        """
        
        if not messages or len(messages) == 0:
            return self._no_urgency()
        
        # Compter messages user consécutifs depuis dernier bot
        consecutive_user = 0
        last_bot_time = None
        last_bot_content = None
        user_msgs_since_bot = []
        
        for msg in reversed(messages):
            # 🔧 Utiliser is_bot au lieu de comparer sender_id
            is_bot = msg.get('profiles', {}).get('is_bot', False)
            
            if is_bot:
                last_bot_time = msg.get('created_at')
                last_bot_content = msg.get('content', '')
                break
            
            consecutive_user += 1
            user_msgs_since_bot.insert(0, msg.get('content', ''))
        
        # Calculer temps d'attente
        minutes_waiting = self._calculate_wait_time(last_bot_time)
        
        # Analyser contexte
        context = self._analyze_context(
            last_bot_content,
            user_msgs_since_bot
        )
        
        # Décision urgence
        is_urgent = (
            consecutive_user >= self.min_consecutive_for_urgent or
            minutes_waiting > self.max_wait_minutes
        )
        
        result = {
            'urgent': is_urgent,
            'consecutive_user_messages': consecutive_user,
            'minutes_waiting': round(minutes_waiting, 1),
            'context': context,
            'last_bot_message': last_bot_content or '',
            'user_messages_since_bot': user_msgs_since_bot
        }
        
        if is_urgent:
            logger.warning("⚠️ RÉPONSE URGENTE NÉCESSAIRE!")
            logger.warning(f"   Consécutifs: {consecutive_user} messages user")
            logger.warning(f"   Attente: {minutes_waiting:.1f} minutes")
            logger.warning(f"   Context: {context}")
        
        return result
    
    def _calculate_wait_time(self, last_bot_time: Optional[str]) -> float:
        """Calcule minutes depuis dernier message bot"""
        if not last_bot_time:
            return 999.0  # Pas de message bot = très longtemps
        
        try:
            # Parser timestamp
            if isinstance(last_bot_time, str):
                if '+' in last_bot_time:
                    last_bot_time = last_bot_time.split('+')[0]
                last_dt = datetime.fromisoformat(last_bot_time)
            else:
                last_dt = last_bot_time
            
            now = datetime.utcnow()
            delta = now - last_dt.replace(tzinfo=None)
            return delta.total_seconds() / 60
        except Exception as e:
            logger.error(f"Erreur calcul temps attente: {e}")
            return 0.0
    
    def _analyze_context(
        self,
        last_bot_msg: Optional[str],
        user_msgs: List[str]
    ) -> str:
        """
        Comprend POURQUOI user envoie plusieurs messages
        
        Returns:
            - USER_CONFUSED: N'a pas compris question bot
            - USER_REPEATING: Répète sa question (bot n'a pas répondu)
            - USER_ELABORATING: Développe sa pensée
            - USER_CLARIFYING: Clarifie sa réponse
            - INITIAL_MESSAGES: Premiers messages
        """
        
        if not last_bot_msg:
            return "INITIAL_MESSAGES"
        
        if len(user_msgs) == 0:
            return "INITIAL_MESSAGES"
        
        # Détecter confusion (user demande clarification)
        confusion_patterns = [
            'quoi', 'comment', 'pourquoi', 'pendant quoi',
            'c\'est quoi', 'tu veux dire', 'je comprends pas',
            '?', 'hein', 'pardon'
        ]
        
        last_user_msg = user_msgs[-1].lower() if user_msgs else ''
        
        # Si dernier bot avait une question mal formulée
        if '?' in last_bot_msg:
            if any(pattern in last_user_msg for pattern in confusion_patterns):
                return "USER_CONFUSED"
        
        # Détecter répétition
        if len(user_msgs) >= 2:
            if user_msgs[-1].lower() == user_msgs[-2].lower():
                return "USER_REPEATING"
            
            # Répétition partielle (même mots-clés)
            words_last = set(user_msgs[-1].lower().split())
            words_prev = set(user_msgs[-2].lower().split())
            if len(words_last & words_prev) / max(len(words_last), 1) > 0.6:
                return "USER_REPEATING"
        
        # Détecter clarification (user corrige/précise)
        clarification_patterns = [
            'non', 'en fait', 'plutôt', 'je veux dire',
            'correction', 'pardon', 'ah non'
        ]
        
        if any(pattern in last_user_msg for pattern in clarification_patterns):
            return "USER_CLARIFYING"
        
        # Par défaut : user élabore sa pensée
        return "USER_ELABORATING"
    
    def _no_urgency(self) -> Dict:
        """Retourne structure 'pas d'urgence'"""
        return {
            'urgent': False,
            'consecutive_user_messages': 0,
            'minutes_waiting': 0.0,
            'context': 'INITIAL_MESSAGES',
            'last_bot_message': '',
            'user_messages_since_bot': []
        }
    
    def build_clarification_prompt(self, urgency_data: Dict) -> str:
        """
        Construit addon pour prompt selon contexte
        """
        
        if not urgency_data['urgent']:
            return ""
        
        context = urgency_data['context']
        last_bot = urgency_data['last_bot_message']
        user_msgs = urgency_data['user_messages_since_bot']
        
        if context == "USER_CONFUSED":
            return f"""
⚠️ SITUATION CRITIQUE : L'utilisateur N'A PAS COMPRIS ta question précédente.

TA DERNIÈRE QUESTION : "{last_bot}"
SES RÉPONSES CONFUSES : {user_msgs}

→ CLARIFIER immédiatement avec empathie et naturel
→ Exemple : "Ah pardon, je me suis mal exprimé(e) ! 😅 Je voulais savoir..."
→ Reformuler clairement ce que tu demandais
→ NE PAS ignorer sa confusion
"""
        
        elif context == "USER_REPEATING":
            return f"""
⚠️ SITUATION : L'utilisateur RÉPÈTE car tu n'as pas répondu.

SA QUESTION RÉPÉTÉE : {user_msgs[-1]}

→ RÉPONDRE DIRECTEMENT à sa question
→ S'excuser subtilement si nécessaire ("Ah désolé(e)...")
→ NE PAS faire comme si de rien n'était
"""
        
        elif context == "USER_CLARIFYING":
            return f"""
ℹ️ L'utilisateur CLARIFIE/CORRIGE sa réponse précédente.

CLARIFICATION : {user_msgs[-1]}

→ PRENDRE EN COMPTE cette clarification
→ Rebondir naturellement ("Ah d'accord, du coup...")
"""
        
        else:  # USER_ELABORATING
            return f"""
ℹ️ L'utilisateur a envoyé {urgency_data['consecutive_user_messages']} messages.

SES MESSAGES : {user_msgs}

→ RÉPONDRE en tenant compte de TOUS ses messages
→ Montrer que tu as bien lu tout ce qu'il a dit
"""
