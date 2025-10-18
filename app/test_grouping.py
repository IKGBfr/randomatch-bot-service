"""
Test du grouping intelligent

Simule des messages rapides pour tester le grouping
"""

import asyncio
import json
from supabase import create_client
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_grouping():
    """
    Test du grouping:
    1. Envoyer 1 message → Doit passer immédiatement
    2. Envoyer 3 messages en <3s → Doivent être groupés
    3. Vérifier dans Redis que le contexte existe
    """
    
    logger.info("=" * 60)
    logger.info("🧪 TEST GROUPING INTELLIGENT")
    logger.info("=" * 60)
    
    # Connexion Supabase
    supabase = create_client(
        settings.supabase_url,
        settings.supabase_service_key
    )
    
    # Récupérer un match de test
    matches = supabase.table('matches').select('*').limit(1).execute()
    
    if not matches.data:
        logger.error("❌ Aucun match trouvé pour le test")
        return
    
    match = matches.data[0]
    match_id = match['id']
    
    # Récupérer les IDs
    bot_id = match['user2_id']  # Supposons user2 = bot
    user_id = match['user1_id']
    
    logger.info(f"📍 Match de test: {match_id}")
    logger.info(f"   Bot: {bot_id}")
    logger.info(f"   User: {user_id}")
    
    # TEST 1: Message unique
    logger.info("\n--- TEST 1: Message unique ---")
    logger.info("Envoi message unique...")
    
    msg1 = supabase.table('messages').insert({
        'match_id': match_id,
        'sender_id': user_id,
        'content': "Test message unique",
        'type': 'text'
    }).execute()
    
    logger.info("✅ Message envoyé")
    logger.info("⏳ Attente 5s (doit passer immédiatement)...")
    await asyncio.sleep(5)
    
    # TEST 2: Messages rapides
    logger.info("\n--- TEST 2: Messages rapides ---")
    logger.info("Envoi 3 messages en <3s...")
    
    messages = [
        "Premier message rapide",
        "Deuxième message rapide",
        "Troisième message rapide"
    ]
    
    for i, content in enumerate(messages, 1):
        msg = supabase.table('messages').insert({
            'match_id': match_id,
            'sender_id': user_id,
            'content': content,
            'type': 'text'
        }).execute()
        
        logger.info(f"✅ Message {i}/3 envoyé")
        
        # Délai court entre messages
        if i < len(messages):
            await asyncio.sleep(0.5)
    
    logger.info("✅ 3 messages envoyés")
    logger.info("⏳ Attente 5s (doivent être groupés)...")
    await asyncio.sleep(5)
    
    logger.info("\n=" * 60)
    logger.info("✅ Test terminé !")
    logger.info("=" * 60)
    logger.info("\n📊 Vérifications à faire manuellement:")
    logger.info("1. Vérifier les logs du bridge pour voir le grouping")
    logger.info("2. Vérifier Redis: redis-cli LLEN bot_messages")
    logger.info("3. Devrait y avoir 2 items dans la queue:")
    logger.info("   - 1er: message unique")
    logger.info("   - 2ème: 3 messages groupés")


if __name__ == "__main__":
    asyncio.run(test_grouping())
