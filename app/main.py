"""
Service unifié avec monitoring, healthcheck et auto-reconnexion.
"""
import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Optional
from aiohttp import web

# Import des services
from app.bridge_intelligence import main as bridge_main
from app.main_worker import main as worker_main

# Configuration logging structuré
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class BotService:
    """Service bot avec monitoring et auto-recovery"""
    
    def __init__(self):
        self.bridge_task: Optional[asyncio.Task] = None
        self.worker_task: Optional[asyncio.Task] = None
        self.health_server: Optional[web.AppRunner] = None
        self.is_running = False
        self.start_time = datetime.utcnow()
        self.restart_count = 0
        
        # Stats
        self.stats = {
            'messages_processed': 0,
            'errors_count': 0,
            'last_error': None,
            'uptime_seconds': 0
        }
    
    async def start(self):
        """Démarre le service complet"""
        logger.info("=" * 70)
        logger.info("🚀 DÉMARRAGE SERVICE BOT")
        logger.info("=" * 70)
        
        self.is_running = True
        
        # Démarrer le healthcheck server
        await self._start_health_server()
        
        # Démarrer les services
        await self._start_services_with_retry()
    
    async def _start_health_server(self):
        """Démarre le serveur de health check pour Railway"""
        app = web.Application()
        app.router.add_get('/health', self._health_handler)
        app.router.add_get('/stats', self._stats_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        # Railway fournit le port via $PORT
        import os
        port = int(os.environ.get('PORT', 8080))
        
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        self.health_server = runner
        logger.info(f"✅ Health check server démarré sur port {port}")
    
    async def _health_handler(self, request):
        """Endpoint health check"""
        bridge_ok = self.bridge_task and not self.bridge_task.done()
        worker_ok = self.worker_task and not self.worker_task.done()
        
        if bridge_ok and worker_ok:
            return web.json_response({
                'status': 'healthy',
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                'services': {
                    'bridge': 'running',
                    'worker': 'running'
                }
            })
        else:
            return web.json_response({
                'status': 'degraded',
                'services': {
                    'bridge': 'running' if bridge_ok else 'stopped',
                    'worker': 'running' if worker_ok else 'stopped'
                }
            }, status=503)
    
    async def _stats_handler(self, request):
        """Endpoint statistiques"""
        self.stats['uptime_seconds'] = (datetime.utcnow() - self.start_time).total_seconds()
        return web.json_response(self.stats)
    
    async def _start_services_with_retry(self):
        """Démarre les services avec retry automatique"""
        while self.is_running:
            try:
                logger.info("🔄 Démarrage des services...")
                
                # Créer les tasks
                self.bridge_task = asyncio.create_task(
                    self._run_with_restart(bridge_main, "Bridge")
                )
                self.worker_task = asyncio.create_task(
                    self._run_with_restart(worker_main, "Worker")
                )
                
                logger.info("✅ Services démarrés")
                
                # Attendre qu'un service crashe
                done, pending = await asyncio.wait(
                    [self.bridge_task, self.worker_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Un service a crashé, redémarrage
                logger.warning("⚠️ Un service s'est arrêté, redémarrage...")
                self.restart_count += 1
                
                # Annuler les tasks restantes
                for task in pending:
                    task.cancel()
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ Erreur: {e}", exc_info=True)
                self.stats['errors_count'] += 1
                self.stats['last_error'] = str(e)
                await asyncio.sleep(10)
    
    async def _run_with_restart(self, service_func, name: str):
        """Exécute un service avec retry automatique"""
        retry_count = 0
        max_retries = 10
        
        while self.is_running and retry_count < max_retries:
            try:
                logger.info(f"▶️  Démarrage {name}...")
                await service_func()
                logger.warning(f"⚠️ {name} s'est arrêté normalement")
                break
            except asyncio.CancelledError:
                logger.info(f"🛑 {name} annulé")
                break
            except Exception as e:
                retry_count += 1
                self.stats['errors_count'] += 1
                self.stats['last_error'] = f"{name}: {str(e)}"
                logger.error(f"❌ {name} erreur (tentative {retry_count}/{max_retries}): {e}", exc_info=True)
                
                if retry_count < max_retries:
                    wait_time = min(2 ** retry_count, 60)
                    logger.info(f"⏳ Attente {wait_time}s avant retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"💀 {name} a atteint le max de retries")
                    break
    
    async def stop(self):
        """Arrête proprement le service"""
        logger.info("🛑 Arrêt du service...")
        self.is_running = False
        
        for task in [self.bridge_task, self.worker_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        if self.health_server:
            await self.health_server.cleanup()
        
        logger.info("✅ Service arrêté proprement")


async def main():
    """Point d'entrée principal"""
    service = BotService()
    
    def signal_handler(sig, frame):
        logger.info(f"📡 Signal {sig} reçu")
        asyncio.create_task(service.stop())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("⚠️ Interruption clavier")
    except Exception as e:
        logger.error(f"💀 Erreur fatale: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())
