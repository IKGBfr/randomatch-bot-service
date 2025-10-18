#!/usr/bin/env python3
"""
🔍 Vérification Complète Pré-Déploiement
Vérifie que tout est prêt pour déployer sur Railway
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(title):
    """Affiche un header formaté"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """Affiche une section"""
    print(f"\n📋 {title}")
    print("-" * 70)


def check_python_version():
    """Vérifie la version Python"""
    print_section("Vérification Python")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (OK)")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro}")
        print(f"   Requis: Python 3.11+")
        return False


def check_files():
    """Vérifie les fichiers critiques"""
    print_section("Vérification Fichiers Critiques")
    
    files = {
        'Procfile': True,
        'requirements.txt': True,
        '.gitignore': True,
        '.env': True,
        'app/__init__.py': True,
        'app/config.py': True,
        'app/bridge_intelligence.py': True,
        'app/worker_intelligence.py': True,
        'app/redis_context.py': True,
        'app/analysis.py': True,
        'app/pre_processing.py': True,
        'app/utils/timing.py': True,
    }
    
    all_ok = True
    for filepath, required in files.items():
        exists = Path(filepath).exists()
        if exists:
            print(f"✅ {filepath}")
        else:
            status = "❌" if required else "⚠️ "
            print(f"{status} {filepath} - {'MANQUANT' if required else 'Optionnel'}")
            if required:
                all_ok = False
    
    return all_ok


def check_env_vars():
    """Vérifie les variables d'environnement"""
    print_section("Vérification Variables d'Environnement")
    
    # Charger .env
    from dotenv import load_dotenv
    load_dotenv()
    
    required = {
        'SUPABASE_URL': 'https://',
        'SUPABASE_SERVICE_KEY': 'eyJ',
        'POSTGRES_CONNECTION_STRING': 'postgresql://',
        'REDIS_URL': 'redis',
        'OPENROUTER_API_KEY': 'sk-or-v1-'
    }
    
    all_ok = True
    for var, prefix in required.items():
        value = os.getenv(var, '')
        if value and value.startswith(prefix):
            masked = value[:15] + '...' if len(value) > 15 else '***'
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: MANQUANT ou INVALIDE")
            all_ok = False
    
    return all_ok


def check_dependencies():
    """Vérifie les dépendances Python"""
    print_section("Vérification Dépendances Python")
    
    deps = [
        'asyncpg',
        'redis',
        'openai',
        'supabase',
        'pydantic',
        'python-dotenv',
        'aiohttp'
    ]
    
    all_ok = True
    for dep in deps:
        try:
            # Essayer d'importer
            if dep == 'python-dotenv':
                __import__('dotenv')
            else:
                __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - NON INSTALLÉ")
            all_ok = False
    
    if not all_ok:
        print("\n💡 Installer avec: pip install -r requirements.txt")
    
    return all_ok


def check_git():
    """Vérifie le statut Git"""
    print_section("Vérification Git")
    
    try:
        # Vérifier repo git
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print("❌ Pas de repo Git initialisé")
            return False
        
        print("✅ Repo Git initialisé")
        
        # Vérifier remote origin
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            remote = result.stdout.strip()
            print(f"✅ Remote origin: {remote}")
        else:
            print("⚠️  Pas de remote origin configuré")
        
        # Vérifier fichiers non commités
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=False
        )
        
        uncommitted = result.stdout.strip()
        if uncommitted:
            lines = uncommitted.split('\n')
            print(f"⚠️  {len(lines)} fichier(s) non commité(s):")
            for line in lines[:5]:
                print(f"     {line}")
            if len(lines) > 5:
                print(f"     ... et {len(lines) - 5} autre(s)")
            return False
        else:
            print("✅ Tous les fichiers commités")
            return True
            
    except FileNotFoundError:
        print("❌ Git n'est pas installé")
        return False


def test_config_import():
    """Test d'import de la configuration"""
    print_section("Test Import Configuration")
    
    try:
        from app.config import settings
        print(f"✅ Config importée")
        print(f"   Environment: {settings.environment}")
        print(f"   Model: {settings.openrouter_model}")
        return True
    except Exception as e:
        print(f"❌ Erreur import config: {e}")
        return False


def main():
    """Exécute toutes les vérifications"""
    print_header("🚀 VÉRIFICATION PRÉ-DÉPLOIEMENT - RandoMatch Bot Service")
    
    results = {
        'Python Version': check_python_version(),
        'Fichiers Critiques': check_files(),
        'Variables Env': check_env_vars(),
        'Dépendances': check_dependencies(),
        'Configuration': test_config_import(),
        'Git Status': check_git(),
    }
    
    # Résumé
    print_header("📊 RÉSUMÉ")
    
    all_passed = True
    for check, passed in results.items():
        emoji = "✅" if passed else "❌"
        print(f"{emoji} {check}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("\n🎉 TOUT EST PRÊT POUR LE DÉPLOIEMENT !\n")
        print("Prochaines étapes:")
        print("  1. git add .")
        print("  2. git commit -m 'feat: Phase 1-2 complete - Intelligence Bot'")
        print("  3. git push origin main")
        print("  4. Déployer sur Railway\n")
        return 0
    else:
        print("\n⚠️  CORRECTIONS NÉCESSAIRES AVANT DÉPLOIEMENT\n")
        print("Résoudre les problèmes marqués ❌ ci-dessus.\n")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Vérification annulée")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
