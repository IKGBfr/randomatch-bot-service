"""
Prompt Builder Intelligent - Construit prompts avec anti-répétition
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Construit des prompts enrichis avec anti-répétition"""
    
    def extract_questions_asked(self, history: List[Dict], bot_name: str = "Camille") -> List[str]:
        """
        Extrait les questions déjà posées par le bot
        
        Args:
            history: Historique complet de la conversation
            bot_name: Nom du bot
            
        Returns:
            Liste des questions posées par le bot
        """
        questions = []
        
        for msg in history:
            if msg.get('profiles', {}).get('is_bot'):
                content = msg['content']
                # Détecter les questions (contient '?')
                if '?' in content:
                    # Extraire chaque question
                    parts = content.split('?')
                    for part in parts[:-1]:  # Exclure la dernière partie (après dernier ?)
                        question = part.strip().split('.')[-1].strip()  # Prendre après dernier point
                        if question:
                            questions.append(question + '?')
        
        return questions
    
    def extract_topics_discussed(self, history: List[Dict]) -> List[str]:
        """
        Extrait les sujets déjà discutés
        
        Args:
            history: Historique complet
            
        Returns:
            Liste des sujets principaux
        """
        topics = []
        keywords = {
            'nature': ['nature', 'forêt', 'montagne', 'ville', 'campagne'],
            'randonnée': ['rando', 'randonnée', 'trek', 'trail', 'gr20'],
            'sport': ['sport', 'escalade', 'vélo', 'course'],
            'travail': ['travail', 'boulot', 'job', 'métier'],
            'loisirs': ['loisirs', 'hobbies', 'passion', 'temps libre'],
            'weekend': ['weekend', 'week-end', 'samedi', 'dimanche']
        }
        
        conversation_text = ' '.join([msg['content'].lower() for msg in history])
        
        for topic, words in keywords.items():
            if any(word in conversation_text for word in words):
                topics.append(topic)
        
        return list(set(topics))
    
    def extract_user_responses(self, history: List[Dict]) -> Dict[str, List[str]]:
        """
        Extrait les réponses de l'utilisateur pour chaque sujet
        
        Args:
            history: Historique complet
            
        Returns:
            Dict {topic: [responses]}
        """
        responses = {
            'nature_preference': [],
            'sports': [],
            'location': [],
            'work': []
        }
        
        # Détecter nature vs ville
        for msg in history:
            if not msg.get('profiles', {}).get('is_bot'):
                content = msg['content'].lower()
                
                if 'nature' in content or 'forêt' in content or 'montagne' in content:
                    responses['nature_preference'].append('nature')
                elif 'ville' in content:
                    responses['nature_preference'].append('ville')
                
                # Sports mentionnés
                if 'rando' in content or 'randonnée' in content:
                    responses['sports'].append('randonnée')
                if 'escalade' in content:
                    responses['sports'].append('escalade')
                
                # Localisation si mentionnée
                # (à implémenter si nécessaire)
        
        return {k: list(set(v)) for k, v in responses.items()}
    
    def build_anti_repetition_context(self, history: List[Dict]) -> str:
        """
        Construit un contexte anti-répétition explicite
        
        Args:
            history: Historique complet
            
        Returns:
            Texte contexte anti-répétition
        """
        questions_asked = self.extract_questions_asked(history)
        topics_discussed = self.extract_topics_discussed(history)
        user_responses = self.extract_user_responses(history)
        
        context = "\n⚠️ RÈGLES ANTI-RÉPÉTITION CRITIQUES:\n\n"
        
        if questions_asked:
            context += "QUESTIONS DÉJÀ POSÉES (NE JAMAIS REPOSER) :\n"
            for q in questions_asked[-10:]:  # 10 dernières questions
                context += f"  - {q}\n"
            context += "\n"
        
        if topics_discussed:
            context += f"SUJETS DÉJÀ DISCUTÉS: {', '.join(topics_discussed)}\n"
            context += "→ Ne pas redemander ce qui a déjà été abordé\n\n"
        
        if user_responses['nature_preference']:
            pref = user_responses['nature_preference'][0]
            context += f"USER A DIT PRÉFÉRER: {pref.upper()}\n"
            context += f"→ Ne JAMAIS redemander nature vs ville\n\n"
        
        if user_responses['sports']:
            sports = ', '.join(user_responses['sports'])
            context += f"SPORTS PRATIQUÉS: {sports}\n"
            context += "→ Ne pas redemander quels sports\n\n"
        
        context += """
📋 INSTRUCTIONS POUR ÉVITER RÉPÉTITIONS:

1. LIS L'HISTORIQUE COMPLET avant de répondre
2. Si une question a déjà été posée, JAMAIS la reposer
3. Si user a déjà répondu à quelque chose, s'en SOUVENIR
4. Rebondir sur ce qui a été dit plutôt que redemander
5. Varier les expressions (pas toujours "Ah...", "Et toi ?")

✅ BON : "Tu m'avais dit que tu aimais la nature, tu vas souvent en forêt ?"
❌ MAUVAIS : "Nature ou ville ?" (déjà demandé 5 fois)

✅ BON : "Cool ! Tu fais d'autres sports ?"
❌ MAUVAIS : "Et toi ?" (répétitif)
"""
        
        return context
    
    def build_full_prompt(
        self,
        bot_profile: Dict,
        memory: Dict,
        history: List[Dict],
        current_message: str,
        analysis: Dict
    ) -> str:
        """
        Construit le prompt complet avec TOUT l'historique et anti-répétition
        
        Args:
            bot_profile: Profil du bot
            memory: Mémoire long-terme
            history: Historique COMPLET (200 messages)
            current_message: Message actuel
            analysis: Analyse du message
            
        Returns:
            Prompt complet
        """
        system_prompt = bot_profile.get('system_prompt', '')
        
        # 1. Mémoire long-terme
        memory_context = f"""
MÉMOIRE DE CETTE PERSONNE:
- Nom: {memory.get('user_name', 'inconnu')}
- Niveau relation: {memory.get('relationship_level', 'stranger')}
- Trust score: {memory.get('trust_score', 0)}/100
- Ton conversation: {memory.get('conversation_tone', 'neutral')}
- Topics préférés: {', '.join(memory.get('preferred_topics', [])) or 'aucun'}
- Topics à éviter: {', '.join(memory.get('topics_to_avoid', [])) or 'aucun'}
"""
        
        # 2. Anti-répétition (CRITIQUE)
        anti_repetition = self.build_anti_repetition_context(history)
        
        # 3. Historique COMPLET (tous les messages chargés)
        logger.info(f"   📚 Historique dans prompt: {len(history)} messages")
        
        history_context = "HISTORIQUE COMPLET DE LA CONVERSATION:\n\n"
        for msg in history:
            name = msg.get('profiles', {}).get('first_name', 'Inconnu')
            content = msg['content']
            history_context += f"{name}: {content}\n"
        
        # 4. Analyse contextuelle
        analysis_context = f"""
ANALYSE DU MESSAGE ACTUEL:
- Urgence: {analysis['urgency']}/5
- Complexité: {analysis['complexity']}/5
- Ton émotionnel: {analysis['emotional_tone']}
- Multi-messages: {analysis.get('requires_multi_messages', False)}
"""
        
        # 5. Instructions adaptatives
        instructions = "\nINSTRUCTIONS:\n"
        
        # Multi-messages : DÉSACTIVÉ TEMPORAIREMENT
        instructions += "\n⚠️ RÈGLE CRITIQUE - FORMAT RÉPONSE:\n"
        instructions += "- TOUJOURS UN SEUL MESSAGE COMPLET\n"
        instructions += "- NE PAS utiliser ||| (désactivé)\n"
        instructions += "- NE JAMAIS répéter ce que tu viens de dire\n"
        instructions += "- NE JAMAIS poser 2x la même question\n\n"
        
        if analysis['urgency'] >= 4:
            instructions += "- Réponds rapidement, c'est urgent\n"
        
        if memory.get('trust_score', 0) >= 70:
            instructions += "- Relation établie, sois authentique et direct\n"
        else:
            instructions += "- Relation naissante, reste naturel mais léger\n"
        
        instructions += "\n💡 VARIÉTÉ EXPRESSIONS:\n"
        instructions += "- Évite 'Ah...' systématique\n"
        instructions += "- Varie les réactions: 'Cool !', 'Vraiment ?', 'Sympa !', 'J'adore !'\n"
        instructions += "- Pas toujours 'Et toi ?' en fin de message\n"
        instructions += "\n⚠️ ANTI-DOUBLON ABSOLU:\n"
        instructions += "- RELIS les questions déjà posées ci-dessus\n"
        instructions += "- Si tu as déjà posé une question, JAMAIS la reposer\n"
        instructions += "- Varie complètement tes questions\n"
        instructions += "- Exemple: Si tu as demandé 'nature ou ville?', ne JAMAIS redemander\n"
        
        # Assembler
        full_prompt = f"""
{system_prompt}

{memory_context}

{anti_repetition}

{history_context}

{analysis_context}

{instructions}

MESSAGE ACTUEL:
{current_message}

TA RÉPONSE:
"""
        
        return full_prompt


# Instance globale
prompt_builder = PromptBuilder()
