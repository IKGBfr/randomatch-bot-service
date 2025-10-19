"""
Exit Manager - Gestion gracieuse de la sortie des bots

Le bot quitte naturellement après X messages en disant qu'il a rencontré quelqu'un
"""
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ExitManager:
    """Gère la logique de sortie des bots"""
    
    # Messages d'exit par catégorie
    EXIT_TEMPLATES = {
        'new_match': [
            "Au fait, j'ai matché avec quelqu'un qui habite pas loin de chez moi 😊",
            "J'ai rencontré quelqu'un sur l'app, on va voir ce que ça donne !",
            "Il y a un gars/une fille qui m'a proposé une rando ce weekend, je vais tenter 🏔️",
            "Je crois que j'ai trouvé quelqu'un avec qui ça match vraiment bien",
            "J'ai discuté avec quelqu'un qui a l'air cool, on va se voir bientôt",
        ],
        'relationship_ended': [
            "Bon ça fait un moment qu'on discute, je vais être honnête...",
            "Je pense qu'il est temps d'être claire avec toi",
            "Alors voilà, je vais te dire franchement",
        ],
        'busy': [
            "Bon je vais être honnête, je suis débordée en ce moment",
            "J'ai pas trop le temps pour l'app ces jours-ci...",
            "En vrai j'ai trop de trucs en ce moment, c'est compliqué",
        ],
        'lost_interest': [
            "Je crois que je vais faire une pause sur l'app",
            "Ça me prend trop de temps tout ça",
            "Je vais me concentrer sur autre chose pour l'instant",
        ],
        'goodbye': [
            "C'était cool de discuter ! Bonne chance pour tes randos 🏔️",
            "Je te souhaite de belles rencontres sur l'app !",
            "À+ et profite bien de tes sorties !",
            "Prends soin de toi et bonne chance 😊",
            "En tout cas c'était sympa d'échanger !",
        ]
    }
    
    def __init__(self, min_messages: int = 15, max_messages: int = 30, exit_chance: float = 0.05):
        self.min_messages = min_messages  # Minimum avant exit possible
        self.max_messages = max_messages  # Maximum absolu
        self.exit_chance = exit_chance  # % chance par message
    
    async def check_should_exit(self, match_id: str, supabase) -> tuple[bool, str]:
        """
        Vérifie si le bot doit quitter cette conversation
        
        Règles:
        - Jours 1-2: Pas d'exit (laisser développer)
        - Jour 3+: Exit direct après premier message
        - Limite messages: Exit à 80% du max
        
        Returns:
            (should_exit: bool, reason: str)
        """
        from datetime import datetime, timezone, timedelta
        
        # Récupérer stats du match
        result = await supabase.fetch_one(
            """
            SELECT bot_messages_count, bot_messages_limit, bot_exit_reason, created_at
            FROM matches
            WHERE id = $1
            """,
            match_id
        )
        
        if not result:
            logger.warning(f"Match {match_id} non trouvé")
            return False, None
        
        # Si déjà exit, ne pas re-exit
        if result['bot_exit_reason']:
            return False, None
        
        count = result['bot_messages_count'] or 0
        limit = result['bot_messages_limit'] or self.max_messages
        
        # Calculer âge du match
        match_created = result['created_at']
        if isinstance(match_created, str):
            match_created = datetime.fromisoformat(match_created.replace('Z', '+00:00'))
        
        now = datetime.now(timezone.utc)
        hours_since_match = (now - match_created).total_seconds() / 3600
        days_since_match = hours_since_match / 24
        
        logger.info(f"   📊 Messages bot: {count}/{limit}")
        logger.info(f"   📅 Âge match: {days_since_match:.1f} jours ({hours_since_match:.1f}h)")
        
        # RÈGLE 1: Pas d'exit pendant les 2 premiers jours
        if days_since_match < 2:
            logger.info(f"   ⏰ Jours 1-2: Pas d'exit (développement relation)")
            return False, None
        
        # RÈGLE 2: Jour 3+ = Exit direct
        if days_since_match >= 3:
            logger.info(f"   🚪 Jour 3+: Exit direct (relation terminée)")
            return True, 'relationship_ended'
        
        # RÈGLE 3: Jour 2-3 = Comportement normal (exit si limite atteinte)
        if count >= limit * 0.8:
            logger.info(f"   🚪 Exit: Limite atteinte ({count} >= {limit * 0.8})")
            return True, 'limit_reached'
        
        # Random exit 5% chance après min_messages (mais pas avant jour 2)
        if count >= self.min_messages:
            if random.random() < self.exit_chance:
                logger.info(f"   🎲 Exit: Random trigger (5% chance)")
                return True, 'random_exit'
        
        return False, None
    
    def generate_exit_sequence(self, reason: str = 'new_match') -> list[dict]:
        """
        Génère 2-3 messages de sortie naturels
        
        Returns:
            Liste de dicts {'text': str, 'delay': float}
        """
        messages = []
        
        # Cas spécial: Jour 3+ (relationship_ended)
        if reason == 'relationship_ended':
            intro = random.choice(self.EXIT_TEMPLATES['relationship_ended'])
            messages.append({
                'text': intro,
                'delay': random.uniform(2, 4)
            })
            
            # Message principal: J'ai rencontré quelqu'un
            main_msg = random.choice(self.EXIT_TEMPLATES['new_match'])
            messages.append({
                'text': main_msg,
                'delay': random.uniform(3, 5)
            })
            
            # Goodbye
            goodbye = random.choice(self.EXIT_TEMPLATES['goodbye'])
            messages.append({
                'text': goodbye,
                'delay': random.uniform(2, 3)
            })
            
            logger.info(f"   📝 Séquence exit Jour 3+ (3 messages)")
            logger.info(f"      1. {intro[:50]}...")
            logger.info(f"      2. {main_msg[:50]}...")
            logger.info(f"      3. {goodbye[:50]}...")
            
            return messages
        
        # Cas normaux (limit_reached, random_exit)
        if reason == 'limit_reached':
            reason_type = random.choice(['new_match', 'busy'])
        elif reason == 'random_exit':
            reason_type = random.choice(['new_match', 'lost_interest'])
        else:
            reason_type = 'new_match'
        
        # Message 1: Annonce la raison
        announce = random.choice(self.EXIT_TEMPLATES[reason_type])
        messages.append({
            'text': announce,
            'delay': random.uniform(3, 6)  # 3-6s avant
        })
        
        # Message 2: Goodbye
        goodbye = random.choice(self.EXIT_TEMPLATES['goodbye'])
        messages.append({
            'text': goodbye,
            'delay': random.uniform(2, 4)  # 2-4s entre les deux
        })
        
        logger.info(f"   📝 Séquence exit générée: {reason_type}")
        logger.info(f"      1. {announce[:50]}...")
        logger.info(f"      2. {goodbye[:50]}...")
        
        return messages
    
    async def mark_as_exited(self, match_id: str, reason: str, supabase):
        """Marque le match comme exit par le bot"""
        try:
            await supabase.execute(
                """
                UPDATE matches 
                SET bot_exit_reason = $1,
                    bot_exited_at = $2
                WHERE id = $3
                """,
                reason,
                datetime.now(),
                match_id
            )
            logger.info(f"   ✅ Match marqué comme exit: {reason}")
        except Exception as e:
            logger.error(f"   ❌ Erreur mark exit: {e}")
    
    async def schedule_unmatch(self, match_id: str, user1_id: str, user2_id: str, 
                              bot_id: str, supabase, delay_minutes: int = 30):
        """
        Programme un unmatch après X minutes
        Note: Implémenté avec un scheduled task séparé
        """
        # Pour l'instant, on log juste
        # Un cron job Railway va gérer le unmatch automatique
        logger.info(f"   🕒 Unmatch programmé dans {delay_minutes}min")
        
        # TODO: Implémenter scheduled_tasks.py si besoin
        # Pour l'instant, le cron va simplement checker bot_exited_at
