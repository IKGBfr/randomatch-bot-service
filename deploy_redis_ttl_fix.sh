#!/bin/bash

echo "🚨 FIX CRITIQUE - Redis TTL trop court"
echo "========================================"
echo ""
echo "Problème : TTL contexte (10s) < Grouping delay (15s)"
echo "Solution : TTL augmenté à 20s"
echo ""

read -p "Déployer ce fix ? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "❌ Annulé"
    exit 1
fi

cd /Users/anthony/Projects/randomatch-bot-service

echo "📦 Commit du fix..."
git add app/redis_context.py
git commit -m "fix(redis): TTL contexte 20s pour survivre au grouping 15s

- CONTEXT_TTL passé de 10s à 20s
- Évite expiration prématurée avant delayed_push()
- Messages ne sont plus perdus après timer grouping"

echo ""
echo "🚀 Push vers Railway..."
git push origin main

echo ""
echo "⏳ Attendre 60 secondes pour rebuild Railway..."
echo "   (Bridge + Worker redémarrent)"
sleep 60

echo ""
echo "✅ Fix déployé !"
echo ""
echo "🧪 Tests à faire :"
echo "1. Envoyer un message dans Flutter"
echo "2. Attendre 20 secondes"
echo "3. Bot doit répondre !"
echo ""
echo "📊 Vérifier logs Railway :"
echo "   railway logs --tail"
echo ""
echo "Logs attendus :"
echo "  📨 Notification reçue"
echo "  ⏰ Nouveau message, démarrage timer 15s"
echo "  [15s plus tard]"
echo "  📦 Grouping: X messages"
echo "  ✅ Message poussé dans queue"
echo "  🤖 TRAITEMENT MESSAGE INTELLIGENT"
