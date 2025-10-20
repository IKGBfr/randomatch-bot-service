#!/bin/bash

# Script de déploiement - Fix Anti-Répétition
# Date: 20 octobre 2025

echo "🚀 Déploiement Fix Anti-Répétition"
echo "==================================="
echo ""

echo "📋 Changements:"
echo "  ✅ MAX_HISTORY_MESSAGES: 50 → 200"
echo "  ✅ Nouveau prompt_builder.py avec anti-répétition"
echo "  ✅ Détection questions déjà posées"
echo "  ✅ Détection réponses utilisateur"
echo "  ✅ Instructions variété expressions"
echo ""

read -p "Déployer sur Railway ? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Déploiement annulé"
    exit 1
fi

echo ""
echo "📦 Git commit..."
git add app/pre_processing.py
git add app/prompt_builder.py
git add app/worker_intelligence.py
git add deploy_anti_repetition.sh

git commit -m "feat: Fix anti-répétition conversations

- Historique: 50 → 200 messages (Grok 4 Fast context window)
- Nouveau prompt_builder avec:
  * Détection questions déjà posées
  * Extraction réponses utilisateur
  * Instructions anti-répétition explicites
  * Variété expressions (pas que 'Ah', 'Et toi ?')
- Intégré dans worker_intelligence.py
- Fix bot qui répète questions et ignore réponses"

echo ""
echo "🚢 Push vers Railway..."
git push origin main

echo ""
echo "✅ Déployé !"
echo ""
echo "⏳ Attendre 30-60s que Railway rebuild..."
echo ""
echo "🧪 Tests:"
echo "  1. railway logs --service worker --tail"
echo "  2. Envoyer message dans l'app"
echo "  3. Vérifier dans logs: '📚 Historique dans prompt: X messages'"
echo "  4. Conversation devrait:"
echo "     - Ne plus répéter questions"
echo "     - Se souvenir des réponses"
echo "     - Varier expressions"
echo ""
echo "🎯 Objectif: Bot cohérent et naturel"
