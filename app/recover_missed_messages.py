"""
Script de récupération des messages sans réponse bot.

Trouve les conversations où :
- Dernier message = user (pas de réponse bot)
- Dans les 3 jours AVANT exit (ou match actif)
- Repousse dans Redis pour retraitement

Usage:
    python -m app.recover_missed_messages

Options:
    --dry-run : Affiche seulement ce qui serait fait (pas de push Redis)
    --days N  : Cherche conversations dans les N derniers jours (défaut: 3)
    --limit N : Limite nombre de conversations à traiter (défaut: 100)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import argparse

from redis.asyncio import Redis
from app.config import Config
from app.supabase_client import SupabaseClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MissedMessagesRecovery:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.supabase: SupabaseClient = None
        self.redis: Redis = None
    
    async def connect(self):
        """Connexion Supabase et Redis"""
        logger.info("🔌 Connexion Supabase...")
        self.supabase = SupabaseClient()
        await self.supabase.connect()
        
        logger.info("🔌 Connexion Redis...")
        self.redis = await Redis.from_url(
            Config.REDIS_URL,
            decode_responses=True
        )
    
    async def disconnect(self):
        """Déconnexion propre"""
        if self.supabase:
            await self.supabase.close()
        if self.redis:
            await self.redis.close()
    
    async def find_missed_conversations(
        self,
        days_back: int = 3,
        limit: int = 100
    ) -> List[Dict]:
        """
        Trouve conversations où dernier message = user sans réponse bot.
        
        Critères :
        - Dernier message de la conversation = user
        - Match actif OU dans les 3 jours avant exit
        - Au moins 1 message échangé
        """
        
        query = """
        WITH last_messages AS (
            SELECT DISTINCT ON (match_id)
                match_id,
                sender_id,
                content,
                created_at,
                id as message_id
            FROM messages
            ORDER BY match_id, created_at DESC
        ),
        bot_profiles AS (
            SELECT id FROM bot_profiles
        )
        
        SELECT 
            m.id as match_id,
            m.user1_id,
            m.user2_id,
            m.created_at as match_created_at,
            m.messages_count,
            m.bot_messages_count,
            m.bot_messages_limit,
            m.bot_exit_reason,
            m.bot_exited_at,
            m.last_message_at,
            lm.message_id,
            lm.sender_id,
            lm.content,
            lm.created_at as last_message_created_at,
            CASE 
                WHEN m.user1_id IN (SELECT id FROM bot_profiles) THEN m.user1_id
                WHEN m.user2_id IN (SELECT id FROM bot_profiles) THEN m.user2_id
                ELSE NULL
            END as bot_id,
            CASE 
                WHEN m.user1_id IN (SELECT id FROM bot_profiles) THEN m.user2_id
                WHEN m.user2_id IN (SELECT id FROM bot_profiles) THEN m.user1_id
                ELSE NULL
            END as user_id
        
        FROM matches m
        INNER JOIN last_messages lm ON m.id = lm.match_id
        
        WHERE 
            -- Dernier message = user (pas bot)
            lm.sender_id NOT IN (SELECT id FROM bot_profiles)
            
            -- Match actif OU dans les X jours avant exit
            AND (
                m.bot_exited_at IS NULL
                OR m.bot_exited_at > NOW() - INTERVAL '%s days'
            )
            
            -- Au moins 1 message échangé
            AND m.messages_count > 0
            
            -- Pas trop récent (laisser time au worker de traiter)
            AND lm.created_at < NOW() - INTERVAL '2 minutes'
        
        ORDER BY lm.created_at DESC
        LIMIT %s
        """ % (days_back, limit)
        
        logger.info(f"🔍 Recherche conversations sans réponse (derniers {days_back} jours)...")
        
        result = await self.supabase.fetch(query)
        
        if not result:
            logger.info("✅ Aucune conversation sans réponse trouvée")
            return []
        
        logger.info(f"📋 {len(result)} conversation(s) sans réponse trouvée(s)")
        
        return result
    
    async def push_to_redis(self, conversation: Dict):
        """Push conversation dans Redis pour retraitement"""
        
        event = {
            "match_id": str(conversation['match_id']),
            "sender_id": str(conversation['user_id']),
            "bot_id": str(conversation['bot_id']),
            "message_id": str(conversation['message_id']),
            "content": conversation['content'],
            "type": "recovery"  # Flag pour identifier récupération
        }
        
        if self.dry_run:
            logger.info(f"[DRY-RUN] Pousserait dans queue: {str(conversation['match_id'])[:8]}")
            return
        
        await self.redis.rpush('bot_messages', json.dumps(event))
        logger.info(f"✅ Poussé dans queue: {str(conversation['match_id'])[:8]}")
    
    async def recover_conversations(
        self,
        days_back: int = 3,
        limit: int = 100
    ):
        """Process principal de récupération"""
        
        try:
            await self.connect()
            
            # Trouver conversations
            conversations = await self.find_missed_conversations(
                days_back=days_back,
                limit=limit
            )
            
            if not conversations:
                return
            
            # Afficher résumé
            logger.info("\n" + "="*60)
            logger.info("📊 RÉSUMÉ DES CONVERSATIONS À RÉCUPÉRER")
            logger.info("="*60)
            
            for conv in conversations:
                logger.info(f"""
Match: {str(conv['match_id'])[:8]}...
├─ Bot: {str(conv['bot_id'])[:8] if conv['bot_id'] else 'None'}...
├─ User: {str(conv['user_id'])[:8] if conv['user_id'] else 'None'}...
├─ Dernier msg user: {conv['last_message_created_at']}
├─ Contenu: "{conv['content'][:50]}..."
├─ Messages count: {conv['messages_count']}
├─ Bot messages: {conv['bot_messages_count']}/{conv['bot_messages_limit']}
├─ Exit: {conv['bot_exit_reason'] or 'Actif'}
└─ Exit date: {conv['bot_exited_at'] or 'N/A'}
""")
            
            logger.info("="*60 + "\n")
            
            # Confirmation si pas dry-run
            if not self.dry_run:
                logger.warning("⚠️  Ces conversations vont être repoussées dans la queue Redis")
                logger.warning("⚠️  Le worker va régénérer des réponses")
                
                response = input("\n❓ Continuer ? (y/N): ")
                if response.lower() != 'y':
                    logger.info("❌ Annulé par l'utilisateur")
                    return
            
            # Push dans Redis
            logger.info(f"\n🔄 Push de {len(conversations)} conversation(s) dans Redis...\n")
            
            for conv in conversations:
                await self.push_to_redis(conv)
                await asyncio.sleep(0.1)  # Rate limiting
            
            logger.info(f"\n✅ {len(conversations)} conversation(s) poussée(s) dans Redis")
            logger.info("⏳ Le worker va les traiter dans les prochaines minutes")
            
        except Exception as e:
            logger.error(f"❌ Erreur: {e}", exc_info=True)
        
        finally:
            await self.disconnect()


async def main():
    """Entry point"""
    
    parser = argparse.ArgumentParser(
        description="Récupère les conversations sans réponse bot"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Affiche seulement ce qui serait fait (pas de push Redis)"
    )
    parser.add_argument(
        '--days',
        type=int,
        default=3,
        help="Cherche conversations dans les N derniers jours (défaut: 3)"
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help="Limite nombre de conversations à traiter (défaut: 100)"
    )
    
    args = parser.parse_args()
    
    logger.info("""
╔══════════════════════════════════════════════════════════╗
║  🔄 RÉCUPÉRATION CONVERSATIONS SANS RÉPONSE BOT         ║
╚══════════════════════════════════════════════════════════╝
""")
    
    if args.dry_run:
        logger.info("🔍 MODE DRY-RUN (aucune modification)")
    
    logger.info(f"📅 Recherche dans les {args.days} derniers jours")
    logger.info(f"📊 Limite: {args.limit} conversations max")
    logger.info("")
    
    recovery = MissedMessagesRecovery(dry_run=args.dry_run)
    await recovery.recover_conversations(
        days_back=args.days,
        limit=args.limit
    )
    
    logger.info("\n✅ Terminé")


if __name__ == "__main__":
    asyncio.run(main())
