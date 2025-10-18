"""
Test avec toutes les variations possibles de connection strings Supabase
"""

import asyncio
import asyncpg


async def test_connection(dsn, description):
    """Test une connection string"""
    print(f"\n🧪 {description}")
    print(f"   DSN: {dsn[:60]}...")
    try:
        conn = await asyncpg.connect(dsn, timeout=10)
        print("   ✅ Connexion réussie!")
        
        # Test LISTEN
        try:
            await conn.add_listener('test_channel', lambda *args: None)
            print("   ✅ LISTEN/NOTIFY supporté!")
            await conn.remove_listener('test_channel', lambda *args: None)
        except Exception as e:
            print(f"   ⚠️  LISTEN non supporté: {e}")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Erreur: {str(e)[:100]}")
        return False


async def main():
    print("=" * 70)
    print("🔍 TEST EXHAUSTIF DES CONNEXIONS SUPABASE")
    print("=" * 70)
    
    password = "ANuNgpYP6_E2FnX"
    project_ref = "mqshuuqdxerisucqjtuh"
    region = "aws-0-eu-central-1"
    
    tests = [
        # Tests avec différents hostnames
        (
            f"postgresql://postgres:{password}@{region}.pooler.supabase.com:5432/postgres",
            "1. Pooler session (5432) - postgres"
        ),
        (
            f"postgresql://postgres.{project_ref}:{password}@{region}.pooler.supabase.com:5432/postgres",
            "2. Pooler session (5432) - postgres.xxx"
        ),
        (
            f"postgresql://postgres:{password}@{region}.pooler.supabase.com:6543/postgres",
            "3. Pooler transaction (6543) - postgres"
        ),
        (
            f"postgresql://postgres.{project_ref}:{password}@{region}.pooler.supabase.com:6543/postgres",
            "4. Pooler transaction (6543) - postgres.xxx"
        ),
        # IPv4 potentielle (AWS eu-central-1)
        (
            f"postgresql://postgres:{password}@3.64.0.0:5432/postgres?sslmode=require",
            "5. Test AWS IPv4 range eu-central-1"
        ),
        # Essayer sans SSL
        (
            f"postgresql://postgres:{password}@{region}.pooler.supabase.com:5432/postgres?sslmode=disable",
            "6. Pooler session sans SSL - postgres"
        ),
        # Avec database spécifique
        (
            f"postgresql://postgres:{password}@{region}.pooler.supabase.com:5432/{project_ref}",
            "7. Pooler avec database = project_ref"
        ),
    ]
    
    print("\n🔄 Lancement des tests...\n")
    
    results = []
    for dsn, desc in tests:
        success = await test_connection(dsn, desc)
        results.append((desc, success))
    
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    
    working = []
    for desc, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {desc}")
        if success:
            working.append(desc)
    
    if working:
        print(f"\n🎉 {len(working)} configuration(s) fonctionnelle(s) trouvée(s) !")
    else:
        print("\n⚠️  Aucune configuration ne fonctionne.")
        print("\n💡 Solutions alternatives:")
        print("   1. Utiliser Supabase Realtime pour les notifications")
        print("   2. Déployer le bridge sur Railway (plus proche du serveur)")
        print("   3. Utiliser un polling court (5-10s) au lieu de LISTEN/NOTIFY")


if __name__ == "__main__":
    asyncio.run(main())
