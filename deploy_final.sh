#!/bin/bash

echo "🚀 Déploiement Complet - Fix Conversations"
echo "=========================================="
echo ""
echo "📋 Changements:"
echo "  ✅ Historique: 50 → 200 messages"
echo "  ✅ Anti-répétition avec détection questions posées"
echo "  ✅ Un seul message par défaut"
echo "  ✅ Multi-messages naturels (20-30% du temps)"
echo "  ✅ Anti-contradiction explicite"
echo "  ✅ Variété expressions"
echo ""

read -p "Déployer sur Railway ? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Annulé"
    exit 1
fi

echo ""
echo "📦 Git commit..."
git add app/pre_processing.py
git add app/prompt_builder.py
git add app/worker_intelligence.py
git add deploy_final.sh

git commit -m "feat: Fix complet conversations bot

- Historique: 200 messages (Grok 4 Fast context)
- Prompt builder anti-répétition:
  * Détecte questions déjà posées
  * Extrait réponses utilisateur
  * Instructions variété expressions
- Format réponse intelligent:
  * Par défaut: 1 message
  * Multi-messages si justifié (|||)
  * Anti-contradiction
- Split uniquement sur ||| explicite

Fix: Bot répète questions, ignore réponses, contradictions"

echo ""
echo "🚢 Push Railway..."
git push origin main

echo ""
echo "✅ Déployé !"
echo ""
echo "⏳ Attendre 60s rebuild..."
echo ""
echo "📋 Tests à faire:"
echo "  1. railway logs --service worker --tail"
echo "  2. Envoyer message app"
echo "  3. Vérifier: '📚 Historique dans prompt: X messages'"
echo "  4. Bot doit:"
echo "     - Ne plus répéter questions"
echo "     - Se souvenir réponses"
echo "     - Envoyer 1 message (ou 2-3 si justifié)"
echo "     - Pas de contradictions"
echo "     - Varier expressions"
