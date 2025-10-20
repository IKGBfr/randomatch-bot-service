#!/bin/bash

echo "=================================================="
echo "🔧 FIX - Méthodes Manquantes SupabaseClient"
echo "=================================================="
echo ""

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "app/supabase_client.py" ]; then
    echo "❌ Erreur : app/supabase_client.py introuvable"
    echo "   Es-tu dans /Users/anthony/Projects/randomatch-bot-service ?"
    exit 1
fi

echo "✅ Fichiers détectés"
echo ""

# Git status
echo "📋 Fichiers modifiés :"
git status --short
echo ""

# Git add
echo "📦 Git add..."
git add app/supabase_client.py app/response_cache.py FIX_MISSING_METHODS.md FIX_MISSING_METHODS_QUICK.md
echo "✅ Fichiers ajoutés"

# Git commit
echo "💾 Git commit..."
git commit -m "fix: Ajouter fetch_one + execute à SupabaseClient, fix typo ResponseCache"

if [ $? -ne 0 ]; then
    echo "⚠️ Rien à commiter (déjà fait ?)"
    echo ""
    echo "Veux-tu forcer le push ? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

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
    echo "⏳ Railway rebuild automatiquement (60s)"
    echo ""
    echo "🧪 DANS 60 SECONDES, TESTE :"
    echo ""
    echo "   1. Flutter → Envoie 'Salut !'"
    echo "   2. Bot répond en 5-15s"
    echo "   3. Logs Railway → Aucune erreur AttributeError"
    echo ""
    echo "📊 LOGS ATTENDUS :"
    echo "   ✅ Check typing OK"
    echo "   ✅ Monitoring messages OK"
    echo "   ✅ Cache doublon OK"
    echo "   ✅ Exit check OK"
    echo "   ✅ Message traité avec succès !"
    echo ""
    echo "❌ ERREURS QUI DISPARAISSENT :"
    echo "   ❌ 'fetch_one' manquant  → ✅ FIXED"
    echo "   ❌ 'execute' manquant    → ✅ FIXED"
    echo "   ❌ '_calculate_...' typo → ✅ FIXED"
    echo ""
    echo "=================================================="
    echo ""
    echo "🔍 Surveiller logs Railway :"
    echo "   railway logs --tail"
    echo ""
else
    echo "❌ Erreur lors du push"
    exit 1
fi
