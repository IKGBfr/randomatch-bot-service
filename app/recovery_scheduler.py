"""
Recovery Scheduler - Service de récupération automatique 24/7.

Tourne en continu sur Railway, check toutes les X heures :
- Trouve conversations sans réponse bot
- Repousse dans Redis pour retraitement
- Logs détaillés pour monitoring

⚙️ Configuration (variables d'environnement) :
- RECOVERY_CHECK_INTERVAL_HOURS : Fréquence check (défaut: 4h)
- RECOVERY_DAYS_BACK : Cherche dans les N derniers jours (défaut: 3)
- RECOVERY_LIMIT : Max conversations par run (défaut: 100)

📊 Monitoring :
- Logs structurés avec timestamp
- Compteur conversations récupérées
- Détails erreurs si échec
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
import sys

from app.config import Config
from app.recover_missed_messages import MissedMessagesRecovery

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RecoveryScheduler:
    """
    Scheduler de récupération automatique.
    Tourne en continu, exécute recovery à intervalles réguliers.
    """
    
    def __init__(
        self,
        check_interval_hours: int = 4,
        days_back: int = 3,
        limit: int = 100
    ):
        self.check_interval_hours = check_interval_hours
        self.days_back = days_back
        self.limit = limit
        
        # Compteurs pour monitoring
        self.total_runs = 0
        self.total_recovered = 0
        self.total_errors = 0
    
    async def run_recovery_once(self):
        """
        Exécute une passe de récupération.
        
        Returns:
            int: Nombre de conversations récupérées
        """
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 RECOVERY RUN #{self.total_runs + 1}")
        logger.info(f"🕐 Timestamp: {datetime.now().isoformat()}")
        logger.info(f"📅 Cherche dans les {self.days_back} derniers jours")
        logger.info(f"📊 Limite: {self.limit} conversations max")
        logger.info(f"{'='*70}\n")
        
        recovery = MissedMessagesRecovery(dry_run=False)
        
        try:
            await recovery.connect()
            
            # Trouver conversations sans réponse
            conversations = await recovery.find_missed_conversations(
                days_back=self.days_back,
                limit=self.limit
            )
            
            if not conversations:
                logger.info("✅ Aucune conversation à récupérer")
                return 0
            
            logger.info(f"📋 {len(conversations)} conversation(s) à récupérer\n")
            
            # Afficher résumé
            for i, conv in enumerate(conversations, 1):
                logger.info(f"[{i}/{len(conversations)}] Match {conv['match_id'][:8]}...")
                logger.info(f"  ├─ Bot: {conv['bot_id'][:8]}...")
                logger.info(f"  ├─ User: {conv['user_id'][:8]}...")
                logger.info(f"  ├─ Dernier msg: {conv['last_message_created_at']}")
                logger.info(f"  ├─ Contenu: \"{conv['content'][:50]}...\"")
                logger.info(f"  └─ Messages: {conv['messages_count']} (bot: {conv['bot_messages_count']}/{conv['bot_messages_limit']})")
            
            logger.info(f"\n🔄 Push de {len(conversations)} conversation(s) dans Redis...\n")
            
            # Push dans Redis
            recovered_count = 0
            for conv in conversations:
                try:
                    await recovery.push_to_redis(conv)
                    recovered_count += 1
                    await asyncio.sleep(0.1)  # Rate limiting
                except Exception as e:
                    logger.error(f"❌ Erreur push {conv['match_id'][:8]}: {e}")
            
            logger.info(f"\n✅ {recovered_count} conversation(s) poussée(s) dans Redis")
            logger.info(f"⏳ Le worker va les traiter dans les prochaines minutes\n")
            
            return recovered_count
            
        except Exception as e:
            logger.error(f"❌ Erreur pendant recovery run: {e}", exc_info=True)
            self.total_errors += 1
            return 0
        
        finally:
            await recovery.disconnect()
    
    async def run_forever(self):
        """
        Boucle principale - tourne indéfiniment.
        """
        
        logger.info(f"""
╔══════════════════════════════════════════════════════════════════╗
║  🛡️  RECOVERY SCHEDULER DÉMARRÉ                                  ║
╚══════════════════════════════════════════════════════════════════╝

⚙️  CONFIGURATION:
  • Check interval: {self.check_interval_hours}h
  • Days back: {self.days_back} jours
  • Limit: {self.limit} conversations/run
  • Première exécution: Immédiate

🎯 OBJECTIF:
  • Rattraper conversations sans réponse bot
  • Filet de sécurité contre bugs/crashes
  • Garantit zéro message perdu

📊 MONITORING:
  • Logs détaillés chaque run
  • Compteurs conversations récupérées
  • Alertes si erreurs répétées
""")
        
        while True:
            try:
                start_time = datetime.now()
                
                # Exécuter recovery
                self.total_runs += 1
                recovered_count = await self.run_recovery_once()
                self.total_recovered += recovered_count
                
                duration = (datetime.now() - start_time).total_seconds()
                
                # Stats globales
                logger.info(f"\n{'='*70}")
                logger.info(f"📊 STATS GLOBALES")
                logger.info(f"{'='*70}")
                logger.info(f"  • Total runs: {self.total_runs}")
                logger.info(f"  • Total récupéré: {self.total_recovered} conversations")
                logger.info(f"  • Total erreurs: {self.total_errors}")
                logger.info(f"  • Durée run: {duration:.2f}s")
                logger.info(f"  • Moyenne/run: {self.total_recovered / self.total_runs:.2f}")
                logger.info(f"{'='*70}\n")
                
                # Prochain run
                next_run = datetime.now().timestamp() + (self.check_interval_hours * 3600)
                next_run_str = datetime.fromtimestamp(next_run).strftime('%Y-%m-%d %H:%M:%S')
                
                logger.info(f"⏰ Prochain run: {next_run_str} (dans {self.check_interval_hours}h)")
                logger.info(f"💤 En attente...\n")
                
                # Attendre jusqu'au prochain run
                await asyncio.sleep(self.check_interval_hours * 3600)
                
            except KeyboardInterrupt:
                logger.info("\n⚠️  Interruption clavier reçue")
                logger.info("🛑 Arrêt gracieux du scheduler...")
                break
            
            except Exception as e:
                logger.error(f"❌ Erreur critique dans boucle principale: {e}", exc_info=True)
                self.total_errors += 1
                
                # Attendre 5 minutes avant retry si erreur
                logger.warning("⏳ Attente 5 min avant retry...")
                await asyncio.sleep(300)
        
        logger.info("✅ Recovery Scheduler arrêté proprement")


async def main():
    """Entry point du service"""
    
    # Charger config depuis variables d'environnement
    check_interval = int(Config.RECOVERY_CHECK_INTERVAL_HOURS)
    days_back = int(Config.RECOVERY_DAYS_BACK)
    limit = int(Config.RECOVERY_LIMIT)
    
    # Créer et démarrer scheduler
    scheduler = RecoveryScheduler(
        check_interval_hours=check_interval,
        days_back=days_back,
        limit=limit
    )
    
    await scheduler.run_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n✅ Service arrêté")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
        sys.exit(1)
