#!/bin/bash

# Script de déploiement - Exit Manager

echo "🚀 Déploiement Exit Manager"
echo "================================"

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "app/exit_manager.py" ]; then
    echo "❌ Erreur: Exécuter depuis randomatch-bot-service/"
    exit 1
fi

# Ajouter les fichiers
echo "📦 Ajout des fichiers..."
git add app/exit_manager.py
git add app/worker_intelligence.py
git add app/scheduled_tasks.py
git add EXIT_SETUP.md

# Commit
echo "💾 Commit..."
git commit -m "feat: exit manager - bot quitte après X messages

- ExitManager: logique exit intelligente (15-30 messages)
- 5% chance random exit après 15 messages
- Messages naturels: 'j'ai rencontré quelqu'un'
- Séquence sortie 2 messages avec délais
- Scheduled task pour unmatch après 30min
- Config: BOT_MIN_MESSAGES, BOT_MAX_MESSAGES, BOT_EXIT_CHANCE"

# Push
echo "🚀 Push vers Railway..."
git push origin main

echo ""
echo "✅ Déploiement lancé!"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Attendre 30-60s pour rebuild Railway"
echo "2. Tester avec conversation 20+ messages"
echo "3. Vérifier logs: railway logs --tail"
echo "4. Configurer cron job (voir EXIT_SETUP.md)"
echo ""
echo "🔍 Logs à chercher:"
echo "   '🚪 Phase 7: Vérification exit'"
echo "   '⚠️ Bot doit quitter'"
echo "   '📤 Envoi séquence exit'"
