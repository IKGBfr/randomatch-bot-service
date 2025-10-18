"""Script de test pour vérifier la configuration."""

import sys
from openai import OpenAI
from app.config import settings


def test_config():
    """Vérifie que toutes les variables d'environnement sont chargées."""
    print("🔍 Vérification de la configuration...")
    print()
    
    # Vérifier Supabase
    print(f"✅ Supabase URL: {settings.supabase_url[:30]}...")
    print(f"✅ Service Key: {settings.supabase_service_key[:20]}...")
    print(f"✅ Postgres: {settings.postgres_connection_string[:40]}...")
    print()
    
    # Vérifier Redis
    print(f"✅ Redis URL: {settings.redis_url[:30]}...")
    print()
    
    # Vérifier OpenRouter
    print(f"✅ OpenRouter Key: {settings.openrouter_api_key[:20]}...")
    print(f"✅ OpenRouter Model: {settings.openrouter_model}")
    print()
    
    # Vérifier Bot Config
    print(f"✅ Typing Speed: {settings.typing_speed_cps} CPS")
    print(f"✅ Thinking Delay: {settings.min_thinking_delay}-{settings.max_thinking_delay}s")
    print()
    
    print("=" * 60)
    print()


def test_openrouter():
    """Test rapide de l'API OpenRouter."""
    print("🤖 Test de connexion OpenRouter...")
    print()
    
    try:
        client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key
        )
        
        print("📡 Envoi d'une requête test...")
        response = client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {
                    "role": "system",
                    "content": "Tu es Camille, une randonneuse passionnée."
                },
                {
                    "role": "user",
                    "content": "Salut ! Dis juste 'Hello Railway' pour tester."
                }
            ],
            temperature=0.8,
            max_tokens=50
        )
        
        bot_reply = response.choices[0].message.content
        print(f"✅ Réponse reçue: {bot_reply}")
        print()
        print("🎉 OpenRouter fonctionne parfaitement !")
        
    except Exception as e:
        print(f"❌ Erreur OpenRouter: {e}")
        sys.exit(1)


def test_supabase_bots():
    """Test récupération des bots depuis Supabase."""
    print("📁 Test récupération bots actifs...")
    print()
    
    try:
        from supabase import create_client
        from app.config import settings
        
        # Créer client avec options
        supabase = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
            options={
                "schema": "public",
                "headers": {"apikey": settings.supabase_service_key}
            }
        )
        
        # Query simple
        result = supabase.table('bot_profiles').select('id, is_active').eq('is_active', True).execute()
        
        print(f"✅ {len(result.data)} bot(s) actif(s) trouvé(s)")
        for bot in result.data:
            print(f"   - Bot ID: {bot['id'][:8]}...")
        print()
        
    except Exception as e:
        print(f"⚠️  Erreur Supabase: {e}")
        print("   (Ce test est optionnel pour Phase 1)")
        print()


def main():
    """Point d'entrée principal."""
    print()
    print("=" * 60)
    print("🚀 RANDOMATCH BOT SERVICE - TEST CONFIGURATION")
    print("=" * 60)
    print()
    
    try:
        test_config()
        test_openrouter()
        test_supabase_bots()
        
        print()
        print("=" * 60)
        print("✨ Tous les tests passés ! Prêt pour Phase 2.")
        print("=" * 60)
        print()
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERREUR: {e}")
        print("=" * 60)
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
