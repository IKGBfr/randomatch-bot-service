#!/bin/bash

echo "============================================================"
echo "🚀 DÉPLOIEMENT URGENT - FIX DUPLICATION"
echo "============================================================"
echo ""

# Vérifier branche
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
    echo "❌ Pas sur main, switch..."
    git checkout main
fi

echo "📝 État des fichiers:"
git status --short
echo ""

# Ajouter les fichiers modifiés
echo "📦 Ajout des fichiers..."
git add app/bridge_intelligence.py
git add app/worker_intelligence.py
git add FIX_DUPLICATION.md
git add FIX_DUPLICATION_SUMMARY.md

echo ""
echo "💾 Commit..."
git commit -m "fix: Élimination duplication messages - 2 réponses → 1

🔧 Solutions implémentées:
1. Bridge: Cooldown 5s après push (évite jobs multiples)
2. Worker: Lock par match_id (évite traitement parallèle)

📊 Résultat attendu:
- User envoie 4 messages rapides
- Bridge groupe en 1 job
- Worker traite 1 fois
- Bot répond 1 fois ✅

Fixes: Cas duplication 2x même réponse observé"

echo ""
echo "🚀 Push vers Railway..."
git push origin main

echo ""
echo "============================================================"
echo "✅ DÉPLOYÉ !"
echo "============================================================"
echo ""
echo "📋 PROCHAINES ÉTAPES:"
echo ""
echo "1. Attendre 60s (rebuild Railway)"
echo "   railway logs --tail"
echo ""
echo "2. Tester avec 4 messages rapides:"
echo "   - 'salut'"
echo "   - 'ca va?'"
echo "   - 'tu fais quoi?'"
echo "   - 'tu aimes la rando?'"
echo ""
echo "3. Vérifier logs Railway:"
echo "   Bridge: '⏰ Cooldown activé'"
echo "   Worker: '⚠️ Match xxx déjà en traitement'"
echo ""
echo "4. Résultat attendu:"
echo "   ✅ 1 SEULE réponse du bot"
echo ""
echo "============================================================"
