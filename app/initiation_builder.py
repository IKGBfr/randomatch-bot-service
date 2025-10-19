"""
Module pour construire le premier message personnalisé après un match.
Génère un message unique basé sur le profil user avec Grok 4 Fast.
"""
import logging
from typing import Dict, Optional
from app.openrouter_client import OpenRouterClient
from app.config import Config

logger = logging.getLogger(__name__)

class InitiationBuilder:
    """Génère le premier message personnalisé pour une initiation post-match"""
    
    def __init__(self):
        self.openrouter = OpenRouterClient()
    
    def build_first_message(
        self,
        bot_profile: Dict,
        user_profile: Dict
    ) -> str:
        """
        Génère le premier message personnalisé avec Grok 4 Fast.
        
        Args:
            bot_profile: Profil du bot (id, first_name, bio, etc.)
            user_profile: Profil user complet avec bio, intérêts, localisation
            
        Returns:
            str: Message personnalisé prêt à envoyer
        """
        try:
            prompt = self._build_prompt(bot_profile, user_profile)
            
            response = self.openrouter.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,  # Plus créatif pour premier message
                max_tokens=100
            )
            
            first_message = response['content'].strip()
            
            logger.info(
                f"✅ Premier message généré pour match "
                f"(bot={bot_profile['first_name']}, user={user_profile['first_name']})"
            )
            
            return first_message
            
        except Exception as e:
            logger.error(f"❌ Erreur génération premier message: {e}")
            # Fallback simple
            return f"Salut {user_profile['first_name']} ! Comment ça va ? 😊"
    
    def _build_prompt(self, bot_profile: Dict, user_profile: Dict) -> str:
        """Construit le prompt pour générer le premier message"""
        
        bot_name = bot_profile['first_name']
        bot_age = self._calculate_age(bot_profile['birth_date'])
        bot_bio = bot_profile.get('bio', '')
        
        user_name = user_profile['first_name']
        user_age = self._calculate_age(user_profile['birth_date'])
        user_bio = user_profile.get('bio', 'Pas de bio')
        user_city = user_profile.get('city', '')
        user_department = user_profile.get('department', '')
        user_hiking_level = user_profile.get('hiking_level', '')
        user_interests = user_profile.get('interests', [])
        
        # Intérêts communs
        bot_interests = bot_profile.get('interests', [])
        common_interests = [i for i in user_interests if i in bot_interests]
        
        prompt = f"""Tu es {bot_name}, {bot_age} ans, passionné(e) de randonnée.
{bot_bio}

Tu viens de matcher avec {user_name}, {user_age} ans.

PROFIL DE {user_name.upper()} :
- Localisation : {user_city}, {user_department}
- Niveau rando : {user_hiking_level}
- Bio : {user_bio}
- Intérêts : {", ".join(user_interests) if user_interests else "Non renseignés"}

INTÉRÊTS COMMUNS : {", ".join(common_interests) if common_interests else "Aucun explicite"}

RÈGLES POUR TON PREMIER MESSAGE :

1. **PRIORITÉ : Rebondis sur SA BIO** si elle contient quelque chose d'exploitable
2. Sinon sur un intérêt commun explicite
3. Sinon sur son niveau de rando s'il est avancé/expert
4. Sinon reste simple : "Salut [prénom] ! Comment ça va ?"

❌ NE JAMAIS :
- Mentionner les photos
- Dire "j'ai vu ta photo"
- Poser une question évidente géo (ex: demander si quelqu'un du 34 connaît les gorges de l'Hérault)

✅ EXEMPLES BONS :
"Salut ! Tu fais aussi du trail ? Tu cours où en général ?"
"Hey ! Expert en rando je vois, tu as fait quoi comme belles courses ?"
"Salut {user_name} ! Comment ça va ?"

❌ EXEMPLES MAUVAIS :
"Belle photo !"
"Tu connais [spot évident de ton département] ?"

**Écris UN SEUL message court (max 2 phrases) :**"""

        return prompt
    
    def _calculate_age(self, birth_date: str) -> int:
        """Calcule l'âge depuis une date de naissance"""
        from datetime import datetime
        
        if not birth_date:
            return 0
        
        try:
            birth = datetime.fromisoformat(birth_date.replace('Z', '+00:00'))
            today = datetime.now()
            age = today.year - birth.year
            if today.month < birth.month or (today.month == birth.month and today.day < birth.day):
                age -= 1
            return age
        except:
            return 0
