"""
🔍 Pre-Deployment Checklist
Vérifie que tout est prêt avant de déployer sur Railway
"""

import os
import sys
from app.config import settings

def check_env_vars():
    """Vérifie que toutes les variables d'environnement sont configurées"""
    print("🔍 Vérification variables d'environnement...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_KEY',
        'POSTGRES_CONNECTION_STRING',
        'REDIS_URL',
        'OPENROUTER_API_KEY'
    ]
    
    missing = []
    for var in required_vars:
        value = getattr(settings, var.lower(), None)
        if not value or value == 'your-value-here':
            missing.append(var)
            print(f"   ❌ {var}: MANQUANT")
        else:
            # Masquer valeur sensible
            masked = value[:10] + '...' if len(value) > 10 else '***'
            print(f"   ✅ {var}: {masked}")
    
    return len(missing) == 0, missing

def check_files():
    """Vérifie que tous les fichiers critiques existent"""
    print("\n📁 Vérification fichiers critiques...")
    
    required_files = [
        'Procfile',
        'requirements.txt',
        '.gitignore',
        'app/__init__.py',
        'app/bridge_intelligence.py',
        'app/worker_intelligence.py',
        'app/redis_context.py',
        'app/analysis.py',
        'app/pre_processing.py',
        'app/utils/timing.py'
    ]
    
    missing = []
    for filepath in required_files:
        if os.path.exists(filepath):
            print(f"   ✅ {filepath}")
        else:
            print(f"   ❌ {filepath}: MANQUANT")
            missing.append(filepath)
    
    return len(missing) == 0, missing

def check_git_status():
    """Vérifie le statut git"""
    print("\n🔧 Vérification Git...")
    
    import subprocess
    
    try:
        # Vérifier s'il y a des fichiers non commités
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print("   ❌ Git n'est pas initialisé")
            return False
        
        uncommitted = result.stdout.strip()
        if uncommitted:
            print("   ⚠️  Fichiers non commités détectés:")
            for line in uncommitted.split('\n')[:5]:  # Max 5 lignes
                print(f"      {line}")
            if len(uncommitted.split('\n')) > 5:
                print(f"      ... et {len(uncommitted.split('\n')) - 5} autres")
            return False
        else:
            print("   ✅ Tous les fichiers sont commités")
            return True
            
    except FileNotFoundError:
        print("   ❌ Git n'est pas installé")
        return False

def check_python_version():
    """Vérifie la version Python"""
    print("\n🐍 Vérification Python...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro}")
        print(f"      Version requise: Python 3.11+")
        return False

def check_dependencies():
    """Vérifie que les dépendances sont installées"""
    print("\n📦 Vérification dépendances...")
    
    required_packages = [
        'asyncpg',
        'redis',
        'openai',
        'supabase',
        'pydantic',
        'dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}: NON INSTALLÉ")
            missing.append(package)
    
    if missing:
        print(f"\n   💡 Installer avec: pip install {' '.join(missing)}")
    
    return len(missing) == 0

def main():
    """Exécute toutes les vérifications"""
    print("=" * 60)
    print("🚀 PRE-DEPLOYMENT CHECKLIST - RandoMatch Bot Service")
    print("=" * 60)
    
    checks = {
        'Python Version': check_python_version(),
        'Environment Variables': check_env_vars()[0],
        'Critical Files': check_files()[0],
        'Dependencies': check_dependencies(),
        'Git Status': check_git_status()
    }
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅ OK" if passed else "❌ ÉCHOUÉ"
        print(f"{status} - {check_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 PRÊT POUR LE DÉPLOIEMENT !")
        print("\nProchaines étapes:")
        print("1. git add .")
        print("2. git commit -m 'feat: Phase 1-2 complete'")
        print("3. git push origin main")
        print("4. Configurer Railway et déployer")
        return 0
    else:
        print("\n⚠️  CORRECTIONS NÉCESSAIRES")
        print("\nRésoudre les problèmes ci-dessus avant de déployer.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
