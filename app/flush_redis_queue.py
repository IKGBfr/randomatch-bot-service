"""
Script pour vider la queue Redis bot_messages

Utilise ceci si tu veux supprimer tous les messages en attente
pour repartir sur une base saine.
"""

import asyncio
from redis.asyncio import Redis
from app.config import Config

async def flush_queue():
    """Vide complètement la queue bot_messages"""
    
    print("🧹 Vidage de la queue Redis 'bot_messages'...")
    
    redis = await Redis.from_url(
        Config.REDIS_URL,
        decode_responses=True
    )
    
    try:
        # Compter messages avant
        count_before = await redis.llen('bot_messages')
        print(f"📊 Messages actuels: {count_before}")
        
        # Vider la queue
        await redis.delete('bot_messages')
        
        # Compter après
        count_after = await redis.llen('bot_messages')
        print(f"✅ Queue vidée ! Messages restants: {count_after}")
        
    finally:
        await redis.aclose()

if __name__ == "__main__":
    asyncio.run(flush_queue())
