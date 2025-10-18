"""
Test de résolution DNS et connexion PostgreSQL avec IPv4 forcé
"""

import asyncio
import asyncpg
import socket


async def resolve_ipv4(hostname):
    """Résoudre le hostname en IPv4 uniquement"""
    print(f"🔍 Résolution DNS pour {hostname}...")
    try:
        # Forcer IPv4 (AF_INET)
        infos = socket.getaddrinfo(hostname, None, socket.AF_INET)
        ipv4_addresses = [info[4][0] for info in infos]
        print(f"   ✅ Adresses IPv4 trouvées: {ipv4_addresses}")
        return ipv4_addresses[0] if ipv4_addresses else None
    except Exception as e:
        print(f"   ❌ Erreur résolution: {e}")
        return None


async def test_connection_with_ip(ip_address, password):
    """Test connexion avec adresse IP directe"""
    print(f"\n🧪 Test connexion avec IP {ip_address}...")
    dsn = f"postgresql://postgres:{password}@{ip_address}:5432/postgres"
    
    try:
        conn = await asyncpg.connect(dsn, timeout=10)
        print("   ✅ Connexion réussie!")
        
        # Test query
        result = await conn.fetchval('SELECT current_database()')
        print(f"   ✅ Database: {result}")
        
        # Test LISTEN
        print("   🧪 Test LISTEN/NOTIFY...")
        await conn.add_listener('test_channel', lambda *args: None)
        print("   ✅ LISTEN fonctionne!")
        
        await conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


async def main():
    print("=" * 60)
    print("🔍 TEST CONNEXION POSTGRESQL AVEC IPv4 FORCÉ")
    print("=" * 60)
    
    password = "ANuNgpYP6_E2FnX"
    hostname = "db.mqshuuqdxerisucqjtuh.supabase.co"
    
    # Résoudre en IPv4
    ipv4 = await resolve_ipv4(hostname)
    
    if ipv4:
        # Tester la connexion avec l'IP
        success = await test_connection_with_ip(ipv4, password)
        
        if success:
            print("\n" + "=" * 60)
            print("✅ SOLUTION TROUVÉE !")
            print("=" * 60)
            print(f"Utilise cette connection string dans ton .env :")
            print(f"POSTGRES_CONNECTION_STRING=postgresql://postgres:{password}@{ipv4}:5432/postgres")
            print("\nOu garde le hostname et configure asyncpg pour forcer IPv4")
    else:
        print("\n❌ Impossible de résoudre le hostname en IPv4")


if __name__ == "__main__":
    asyncio.run(main())
