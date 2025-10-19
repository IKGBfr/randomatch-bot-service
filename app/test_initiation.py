"""
Script de test pour le système d'initiation post-match.
Crée un match test et vérifie que l'initiation fonctionne.
"""
import asyncio
import sys
from datetime import datetime
from supabase import create_client
from app.config import Config
from app.match_monitor import MatchMonitor

async def test_initiation():
    """Test complet du système d'initiation"""
    
    print("\n🧪 TEST INITIATION POST-MATCH")
    print(f"Mode: {'TEST (immédiat)' if Config.TEST_MODE else 'PRODUCTION'}")
    print(f"User test: {Config.TEST_USER_ID}")
    print(f"Bot Camille: {Config.BOT_CAMILLE_ID}")
    print(f"Bot Paul: {Config.BOT_PAUL_ID}\n")
    
    # Connexion Supabase
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_KEY)
    
    # Créer match test
    print("📝 Création match test...")
    match_response = supabase.table('matches').insert({
        'user1_id': Config.BOT_CAMILLE_ID,  # Camille
        'user2_id': Config.TEST_USER_ID      # Albert
    }).execute()
    
    match = match_response.data[0]
    print(f"✅ Match créé: {match['id']}")
    
    # Process match
    print("\n🤖 Traitement par MatchMonitor...")
    monitor = MatchMonitor(supabase)
    initiation_id = await monitor.process_new_match(match)
    
    if initiation_id:
        print(f"✅ Initiation créée: {initiation_id}")
        
        # Récupérer initiation
        init_response = supabase.table('bot_initiations').select('*').eq(
            'id', initiation_id
        ).single().execute()
        
        init = init_response.data
        print(f"\n📋 Détails initiation:")
        print(f"  Match: {init['match_id']}")
        print(f"  Bot: {init['bot_id']}")
        print(f"  User: {init['user_id']}")
        print(f"  Scheduled: {init['scheduled_for']}")
        print(f"  Status: {init['status']}")
        print(f"  Message: {init['first_message']}")
        
        # Si TEST_MODE, vérifier que scheduled_for est immédiat
        scheduled = datetime.fromisoformat(init['scheduled_for'].replace('Z', '+00:00'))
        now = datetime.now(scheduled.tzinfo)
        delay_seconds = (scheduled - now).total_seconds()
        
        print(f"\n⏱️ Délai avant envoi: {delay_seconds:.1f}s")
        
        if Config.TEST_MODE and delay_seconds > 120:
            print("❌ ERREUR: Délai trop long en TEST_MODE")
        else:
            print("✅ Délai correct")
        
        # Attendre et envoyer
        if delay_seconds < 120:
            print(f"\n⏳ Attente {delay_seconds:.1f}s puis envoi...")
            await asyncio.sleep(max(0, delay_seconds))
            
            print("📤 Envoi initiation...")
            await monitor.check_pending_initiations()
            
            # Vérifier status
            check_response = supabase.table('bot_initiations').select(
                'status, sent_at'
            ).eq('id', initiation_id).single().execute()
            
            if check_response.data['status'] == 'sent':
                print(f"✅ Message envoyé: {check_response.data['sent_at']}")
            else:
                print(f"❌ Échec envoi: {check_response.data['status']}")
        
    else:
        print("❌ Pas d'initiation créée")
    
    print("\n✅ Test terminé\n")

if __name__ == "__main__":
    asyncio.run(test_initiation())
