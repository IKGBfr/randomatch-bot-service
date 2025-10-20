#!/bin/bash

echo "🚀 Déploiement Exit Timing"
echo "================================"

cd /Users/anthony/Projects/randomatch-bot-service

git add app/exit_manager.py
git commit -m "feat: exit temporel intelligent

- Jours 1-2: Pas d'exit (laisser développer relation)
- Jour 3+: Exit direct avec séquence 3 messages
- Limite messages: Exit à 80% du max (jour 2-3)
- Messages adaptés selon timing exit"

git push origin main

echo ""
echo "✅ Déployé!"
echo ""
echo "📋 Logique exit:"
echo "  • Jour 1-2: Aucun exit"
echo "  • Jour 3+: Exit automatique au prochain message"
echo "  • 15-30 messages: Exit si limite atteinte"
