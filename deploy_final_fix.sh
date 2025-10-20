#!/bin/bash

# 🚨 FIX DÉFINITIF - Grouping + Anti-Répétition
# Date: 20 octobre 2025

echo "🚨 FIX DÉFINITIF - GROUPING + ANTI-RÉPÉTITION"
echo "=============================================="
echo ""

echo "📋 Modifications appliquées :"
echo ""
echo "1. ✅ Bridge : Premier message attend aussi le timer"
echo "   - Plus de push immédiat du 1er message"
echo "   - Tous les messages attendent 8s pour grouping"
echo ""
echo "2. ✅ Bridge : Timer marqué comme démarré"
echo "   - Évite création de timers multiples"
echo ""
echo "3. ✅ Worker : Split multi-messages DÉSACTIVÉ"
echo "   - Force UN SEUL message (pas de split par |||)"
echo "   - Évite doublons contradictoires"
echo ""
echo "4. ✅ Prompt : Instructions anti-répétition RENFORCÉES"
echo "   - Consignes explicites ANTI-DOUBLON"
echo "   - Instructions de relecture"
echo ""

echo "⚠️  IMPORTANT : Le fix est AGRESSIF pour stopper les doublons"
echo "   Multi-messages sera réactivé PLUS TARD après validation"
echo ""

read -p "Déployer maintenant ? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Déploiement annulé"
    exit 1
fi

echo ""
echo "🚀 Démarrage déploiement..."
echo ""

# Commit
git add .
git commit -m "fix: Grouping définitif + anti-répétition renforcée

- Bridge attend TOUJOURS 8s avant push (même 1er message)
- Timer marqué comme démarré dans contexte Redis
- Split multi-messages DÉSACTIVÉ temporairement
- Instructions anti-répétition renforcées dans prompt

Résout:
- Messages rapides groupés correctement
- Plus de doublons contradictoires
- Plus de questions répétées 2x"

echo ""
echo "📦 Push vers Railway..."
git push origin main

echo ""
echo "✅ DÉPLOYÉ !"
echo ""
echo "⏳ Attendre 60s pour rebuild Railway..."
echo ""
echo "🧪 Tests à faire après rebuild :"
echo ""
echo "Test 1 - Messages Rapides (<8s) :"
echo "  1. Envoyer 'Salut'"
echo "  2. Envoyer 'ça va ?' immédiatement"
echo "  ✅ Bot doit répondre 1 SEULE fois (groupés)"
echo ""
echo "Test 2 - Question Déjà Posée :"
echo "  1. Attendre que bot pose question X"
echo "  2. Répondre"
echo "  3. Vérifier que bot ne repose PAS X"
echo ""
echo "Test 3 - Pas de Contradictions :"
echo "  1. Envoyer message"
echo "  ✅ Bot ne doit PAS se contredire dans sa réponse"
echo ""
echo "📊 Vérifier logs Railway :"
echo "  railway logs --service bridge --tail"
echo "  railway logs --service worker --tail"
echo ""
echo "Chercher :"
echo "  🔄 Grouping: X messages → OK"
echo "  ⏰ Nouveau message, démarrage timer → OK"
echo "  ➡️ Un seul message (split désactivé) → OK"
echo ""
