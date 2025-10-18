"""
Test de connexion PostgreSQL directe avec différentes configurations
"""

import asyncio
import asyncpg


async def test_connection(dsn, description):
    """Test une connection string"""
    print(f"\n🧪 Test: {description}")
    print(f"   DSN: {dsn[:50]}...")
    try:
        conn = await asyncpg.connect(dsn, timeout=10)
        print("   ✅ Connexion réussie!")
        
        # Test simple query
        result = await conn.fetchval('SELECT 1')
        print(f"   ✅ Query test: {result}")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


async def main():
    print("=" * 60)
    print("🔍 TEST DES CONNEXIONS POSTGRESQL")
    print("=" * 60)
    
    password = "ANuNgpYP6_E2FnX"
    project_ref = "mqshuuqdxerisucqjtuh"
    
    tests = [
        # Test 1: Pooler port 5432 avec postgres
        (
            f"postgresql://postgres:{password}@aws-0-eu-central-1.pooler.supabase.com:5432/postgres",
            "Pooler port 5432 (session mode) - username: postgres"
        ),
        # Test 2: Pooler port 5432 avec postgres.xxx
        (
            f"postgresql://postgres.{project_ref}:{password}@aws-0-eu-central-1.pooler.supabase.com:5432/postgres",
            "Pooler port 5432 (session mode) - username: postgres.xxx"
        ),
        # Test 3: Connexion directe IPv4 only
        (
            f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres",
            "Connexion directe - db.xxx.supabase.co"
        ),
        # Test 4: Pooler port 6543 avec postgres.xxx
        (
            f"postgresql://postgres.{project_ref}:{password}@aws-0-eu-central-1.pooler.supabase.com:6543/postgres",
            "Pooler port 6543 (transaction mode) - username: postgres.xxx"
        ),
    ]
    
    results = []
    for dsn, desc in tests:
        success = await test_connection(dsn, desc)
        results.append((desc, success))
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    for desc, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {desc}")
    
    print("\n💡 Pour LISTEN/NOTIFY, il faut une connexion qui reste ouverte")
    print("   (pas le pooler en mode transaction)")


if __name__ == "__main__":
    asyncio.run(main())
