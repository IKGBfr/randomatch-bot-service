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
        analysis: Dict,
        clarification_context: Dict = None  # 🆕 NOUVEAU
    ) -> str:
        """
        Construit le prompt complet avec TOUT l'historique et anti-répétition
        
        Args:
            bot_profile: Profil du bot
            memory: Mémoire long-terme
            history: Historique COMPLET (200 messages)
            current_message: Message actuel
            analysis: Analyse du message
            clarification_context: Contexte de clarification (si USER_CONFUSED)
            
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
        
        # CLARIFIER qui est qui dans l'historique
        bot_name = bot_profile.get('first_name', 'Camille')
        
        history_context = f"""HISTORIQUE COMPLET DE LA CONVERSATION:
(Tu es {bot_name}. Les messages marqués "TOI:" sont TES messages passés)

"""
        
        for msg in history:
            sender_name = msg.get('profiles', {}).get('first_name', 'Inconnu')
            is_bot = msg.get('profiles', {}).get('is_bot', False)
            content = msg['content']
            
            if is_bot:
                # C'est le bot qui a parlé
                history_context += f"TOI ({bot_name}): {content}\n"
            else:
                # C'est l'user qui a parlé
                history_context += f"{sender_name}: {content}\n"
        
        history_context += "\n"
        
        # 4. Analyse contextuelle
        analysis_context = f"""
ANALYSE DU MESSAGE ACTUEL:
- Urgence: {analysis['urgency']}/5
- Complexité: {analysis['complexity']}/5
- Ton émotionnel: {analysis['emotional_tone']}
- Multi-messages: {analysis.get('requires_multi_messages', False)}
"""
        
        # 5. 🆕 Contexte de clarification (si USER_CONFUSED)
        clarification_instructions = ""
        
        if clarification_context:
            clarification_instructions = f"""

🚨 SITUATION SPÉCIALE - USER CONFUS:

L'utilisateur a envoyé plusieurs messages car il n'a PAS COMPRIS ta question précédente.

TA QUESTION PRÉCÉDENTE:
"{clarification_context.get('last_bot_message', 'N/A')}"

SES RÉPONSES CONFUSES:
"""
            for msg in clarification_context.get('confused_messages', []):
                clarification_instructions += f"- \"{msg}\"\n"
            
            clarification_instructions += """

🎯 TON OBJECTIF:
1. CLARIFIER ta question précédente avec empathie
2. REFORMULER de manière plus claire
3. NE PAS t'excuser excessivement (reste naturel)
4. Exemple: "Ah pardon, je me suis mal exprimé ! Je voulais dire..."
5. Exemple: "Haha désolé, je voulais savoir..."

⚠️ TON: Léger, pas trop formel, un peu d'auto-dérision OK
"""
        
        # 6. Instructions adaptatives
        instructions = "\nINSTRUCTIONS:\n"
        
        # 🆕 CONTEXTE CRITIQUE : Comprendre la situation actuelle
        instructions += "\n🚨 CONTEXTE ACTUEL CRITIQUE:\n"
        
        # Identifier le dernier message du bot
        bot_messages = [msg for msg in history if msg.get('profiles', {}).get('is_bot')]
        if bot_messages:
            last_bot_msg = bot_messages[-1]['content']
            instructions += f"- TON DERNIER MESSAGE était: \"{last_bot_msg}\"\n"
            instructions += "- L'user RÉPOND maintenant à ce message\n"
            instructions += "- NE PAS répéter ce que tu viens de dire\n"
            
            # Cas spécifique : Bot a initié avec "Salut"
            if 'salut' in last_bot_msg.lower() or 'hello' in last_bot_msg.lower() or 'hey' in last_bot_msg.lower():
                instructions += "- Tu as DÉJÀ dit bonjour/salut\n"
                instructions += "- NE PAS redire 'Salut' maintenant\n"
                instructions += "- Si user demande 'Et toi ?', RÉPONDS À LA QUESTION\n"
                instructions += "- Exemple BON: 'Ça va bien ! Et toi ?' ou 'Bien, merci'\n"
                instructions += "- Exemple MAUVAIS: 'Salut ! Et toi ?' (tu as déjà dit salut!)\n\n"
        else:
            instructions += "- C'est possiblement le début de la conversation\n\n"
        
        instructions += "\n"
        # Multi-messages : DÉSACTIVÉ TEMPORAIREMENT
        instructions += "\n⚠️ RÈGLE CRITIQUE - FORMAT RÉPONSE:\n"
        instructions += "- TOUJOURS UN SEUL MESSAGE COMPLET\n"
        instructions += "- NE PAS utiliser ||| (désactivé)\n"
        instructions += "- NE JAMAIS répéter ce que tu viens de dire\n"
        instructions += "- NE JAMAIS poser 2x la même question\n\n"
        
        # CRITIQUE: Adaptation selon phase conversation
        message_count = len(history)
        instructions += "\n🚨 RÈGLE ULTRA-CRITIQUE - ADAPTATION STYLE:\n"
        
        if message_count == 0:
            instructions += "- PREMIER MESSAGE: Tu peux commencer par 'Salut [Prénom] !'\n"
            instructions += "- C'est normal de se présenter au début\n"
        elif message_count < 5:
            instructions += "- DÉBUT DE CONVERSATION (2-5 messages):\n"
            instructions += "- NE PAS recommencer par 'Salut [Prénom]'\n"
            instructions += "- Tu as déjà dit bonjour, continue naturellement\n"
            instructions += "- Commence directement par ta réponse\n"
        else:
            instructions += "- CONVERSATION EN COURS (5+ messages):\n"
            instructions += "- NE JAMAIS JAMAIS commencer par 'Salut [Prénom]'\n"
            instructions += "- Vous vous parlez déjà depuis un moment\n"
            instructions += "- Commence DIRECTEMENT par ta réponse\n"
            instructions += "- Exemple BON: 'Ah cool !', 'Vraiment ?', 'J'adore'\n"
            instructions += "- Exemple MAUVAIS: 'Salut Albert', 'Hello', 'Hey'\n"
        
        instructions += "\n"
        
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
        instructions += "- RELIS l'historique COMPLET ci-dessus\n"
        instructions += "- IDENTIFIE ce que TU (TOI:) as déjà dit\n"
        instructions += "- NE JAMAIS répéter tes propres messages\n"
        instructions += "- Si tu as déjà posé une question, JAMAIS la reposer\n"
        instructions += "- Varie complètement tes questions\n"
        instructions += "- Exemple: Si tu as demandé 'nature ou ville?', ne JAMAIS redemander\n"
        instructions += "\n🎯 RÈGLE D'OR:\n"
        instructions += "- Si user répond à TA question, reconnais-le et continue naturellement\n"
        instructions += "- Si user te pose une question, RÉPONDS-Y directement\n"
        instructions += "- Exemple: User dit 'Et toi ?' → Réponds 'Ça va bien !' ou similaire\n"
        instructions += "- NE PAS renvoyer la question si c'est toi qui l'as posée en premier\n"
        instructions += "\n🧠 COMPRÉHENSION CONTEXTUELLE CRITIQUE:\n"
        instructions += "- Quand l'user dit 'MON [nombre]ème message', il parle de SES messages UNIQUEMENT\n"
        instructions += "- NE PAS compter les messages marqués 'TOI (Camille):' dans ce calcul\n"
        instructions += "- COMPTER SEULEMENT les messages de l'user (sans 'TOI:')\n"
        instructions += "- Exemple: Si user dit 'mon 4ème message', compte ses 4 messages à lui\n"
        instructions += "- ❌ MAUVAIS: Compter tous les messages de la conversation\n"
        instructions += "- ✅ BON: Compter seulement les lignes qui commencent par le prénom de l'user\n"
        instructions += "\n💡 PRONOMS PERSONNELS:\n"
        instructions += "- 'MON/MES' = appartient à l'user\n"
        instructions += "- 'TON/TES' = t'appartient à TOI (le bot)\n"
        instructions += "- 'NOTRE/NOS' = vous deux ensemble\n"
        instructions += "- User dit 'mon projet' → C'est SON projet, pas le tien\n"
        instructions += "- User dit 'notre conversation' → C'est vous deux\n"
        
        # 7. CONTEXTE HORAIRE - CRITIQUE
        from datetime import datetime
        import pytz
        
        paris_tz = pytz.timezone('Europe/Paris')
        current_time = datetime.now(paris_tz)
        hour = current_time.hour
        minute = current_time.minute
        
        time_context = f"\n🕐 CONTEXTE HORAIRE - IL EST {hour:02d}h{minute:02d} :\n"
        
        if 0 <= hour < 6:
            time_context += "- 🌙 NUIT : Tu es au lit ou sur ton canapé\n"
            time_context += "- ❌ NE PAS dire que tu travailles !\n"
            time_context += "- ✅ Tu peux dire : 'Je regarde une série', 'Je suis sur mon tel', 'Je devrais dormir'\n"
        elif 6 <= hour < 9:
            time_context += "- ☕ MATIN : Tu te prépares ou petit-déjeuner\n"
            time_context += "- ✅ Tu peux mentionner : café, réveil, préparation\n"
        elif 9 <= hour < 12:
            time_context += "- 💼 MATINÉE : Tu es au travail\n"
            time_context += "- ✅ Tu peux dire que tu travailles, tu fais une pause\n"
        elif 12 <= hour < 14:
            time_context += "- 🍽️ MIDI : Pause déjeuner\n"
            time_context += "- ✅ Tu peux parler de manger, pause café\n"
        elif 14 <= hour < 18:
            time_context += "- 💼 APRÈS-MIDI : Tu es au travail\n"
            time_context += "- ✅ Tu peux dire que tu bosses, journée longue\n"
        elif 18 <= hour < 21:
            time_context += "- 🏠 DÉBUT SOIRÉE : Tu rentres ou tu es rentrée\n"
            time_context += "- ✅ Tu peux mentionner : sport, courses, cuisine, détente\n"
        else:  # 21-24
            time_context += "- 🛋️ SOIRÉE : Tu es CHEZ TOI, détendue\n"
            time_context += "- ❌ NE JAMAIS dire que tu travailles !\n"
            time_context += "- ✅ Tu peux dire : 'Je suis posée', 'Tranquille chez moi', 'Je regarde Netflix'\n"
            time_context += "- ✅ Ou : 'Rien de spécial', 'Je chill', 'Sur mon canapé'\n"
        
        time_context += "\n"
        
        # Assembler
        full_prompt = f"""
{system_prompt}

{memory_context}

{anti_repetition}

{history_context}

{analysis_context}

{time_context}

{clarification_instructions}

{instructions}

MESSAGE ACTUEL:
{current_message}

TA RÉPONSE:
"""
        
        return full_prompt


# Instance globale
prompt_builder = PromptBuilder()
