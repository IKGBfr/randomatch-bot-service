#!/bin/bash

echo "=================================================="
echo "🚨 FIX - Bot Ne Répond Pas"
echo "=================================================="
echo ""

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "app/unified_service.py" ]; then
    echo "❌ Erreur : app/unified_service.py introuvable"
    echo "   Es-tu dans /Users/anthony/Projects/randomatch-bot-service ?"
    exit 1
fi

echo "✅ Fichiers détectés"
echo ""

# Rendre start.sh exécutable
chmod +x start.sh
echo "✅ start.sh rendu exécutable"

# Git add
echo "📦 Git add..."
git add app/unified_service.py start.sh FIX_BOT_NO_RESPONSE.md FIX_BOT_NO_RESPONSE_QUICK.md
echo "✅ Fichiers ajoutés"

# Git commit
echo "💾 Git commit..."
git commit -m "fix: Service unifié bridge+worker pour Railway"
echo "✅ Commit créé"

# Git push
echo "🚀 Git push..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✅ DÉPLOYÉ SUR GITHUB"
    echo "=================================================="
    echo ""
    echo "⏳ Railway va rebuild automatiquement (60s)"
    echo ""
    echo "🎯 MAINTENANT, VAS DANS RAILWAY DASHBOARD :"
    echo ""
    echo "   1. Va dans Settings → Deploy"
    echo "   2. Change 'Start Command' en :"
    echo ""
    echo "      python -m app.unified_service"
    echo ""
    echo "   3. Save et attends rebuild"
    echo ""
    echo "🧪 PUIS TESTE :"
    echo "   Flutter → Envoie 'Salut !' → Bot répond en 5-15s"
    echo ""
    echo "=================================================="
else
    echo "❌ Erreur lors du push"
    exit 1
fi
