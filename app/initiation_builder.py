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
        
        prompt = f"""Tu discutes naturellement sur une app de rencontre. Profil de {user_name} :
Bio : {user_bio}
Intérêts : {", ".join(user_interests[:3]) if user_interests else "Aucun"}
Niveau rando : {user_hiking_level}

Écris UN message d'accroche court comme tu écrirais vraiment sur ton tel. Pas construit, pas eager.

✅ OPTIONS (choisis 1) :
1. Si sa bio a un truc cool → Réagis simplement
2. Si intérêt commun → Mentionne-le casual
3. Sinon → Juste "Salut {user_name} !" + question simple

❌ ÉVITE :
- Phrases longues/construites
- "me parle", "m'interpelle", "résonne"
- Essayer de tout dire d'un coup
- Trop d'enthousiasme

✅ BONS (courts, directs) :
"Salut ! Tu cours où en général ?"
"Hey ! Comment ça va ?"
"Salut {user_name} ! Ça va ?"
"Cool le trail ! Tu fais quoi comme distances ?"
"Salut ! T'es de {user_city} ?"
"Hey ! Tu randos où d'habitude ?"

Écris comme tu parlerais. 1 phrase, max 2. Décontracté.

Message :"""

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
