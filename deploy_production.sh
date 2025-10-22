#!/bin/bash

# Script de déploiement automatisé pour Railway
# Usage: ./deploy_production.sh

set -e  # Arrêter en cas d'erreur

echo "═══════════════════════════════════════════════════════════"
echo "🚀 DÉPLOIEMENT PRODUCTION - Bot RandoMatch"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "app/robust_service.py" ]; then
    echo "❌ Erreur: Fichier robust_service.py introuvable"
    echo "   Assurez-vous d'être dans le répertoire randomatch-bot-service"
    exit 1
fi

# Vérifier que Git est configuré
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Erreur: Ce n'est pas un dépôt Git"
    exit 1
fi

echo "📋 Vérification des fichiers critiques..."
echo ""

# Vérifier les fichiers clés
files=(
    "app/robust_service.py"
    "app/bridge_intelligence.py"
    "app/main_worker.py"
    "Procfile"
    "requirements.txt"
    ".env"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file manquant"
        exit 1
    fi
done

echo ""
echo "🔍 Vérification du Procfile..."
cat Procfile
echo ""

echo "📦 Vérification des dépendances..."
grep -E "aiohttp|asyncpg|redis|supabase|openai" requirements.txt
echo ""

echo "🔄 Status Git..."
git status --short
echo ""

read -p "📤 Voulez-vous commiter et pusher ces changements ? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "💾 Commit des changements..."
    git add .
    
    # Générer un message de commit
    COMMIT_MSG="feat: Production-ready bot service with auto-recovery and monitoring

- Added robust_service.py with health checks
- Auto-restart on failure with exponential backoff
- Health check endpoints: /health and /stats
- Comprehensive error handling and logging
- Graceful shutdown on SIGTERM/SIGINT
- Updated Procfile to use robust service
- Production deployment guide included
"
    
    git commit -m "$COMMIT_MSG" || echo "ℹ️  Rien à commiter"
    
    echo ""
    echo "🚀 Push vers GitHub..."
    git push origin main
    
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "✅ DÉPLOIEMENT INITIÉ"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "📍 Prochaines étapes :"
    echo ""
    echo "1. Va sur https://railway.app"
    echo "2. Vérifie que le déploiement est en cours"
    echo "3. Attends que le status soit 'Active'"
    echo "4. Vérifie les logs : railway logs --tail"
    echo "5. Teste le health check : curl https://ton-app.railway.app/health"
    echo "6. Teste le bot dans ton app RandoMatch"
    echo ""
    echo "📖 Guide complet : PRODUCTION_DEPLOYMENT.md"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    
else
    echo "❌ Déploiement annulé"
    exit 1
fi
