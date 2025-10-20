#!/bin/bash

# Script de déploiement - Fix Initiation Après Conversation
# Date: 20 octobre 2025

set -e  # Exit si erreur

echo "🚀 DÉPLOIEMENT FIX INITIATION APRÈS CONVERSATION"
echo "================================================="
echo ""

# Vérifier qu'on est dans le bon dossier
if [ ! -f "app/match_monitor.py" ]; then
    echo "❌ Erreur : Pas dans le dossier randomatch-bot-service"
    exit 1
fi

echo "📁 Dossier OK : $(pwd)"
echo ""

# Vérifier que le fix est bien là
if grep -q "_check_existing_messages" app/match_monitor.py; then
    echo "✅ Fix présent dans match_monitor.py"
else
    echo "❌ Fix manquant dans match_monitor.py"
    exit 1
fi

echo ""
echo "📝 Ajout fichiers au commit..."
git add app/match_monitor.py \
        FIX_INITIATION_APRES_CONVERSATION.md \
        FIX_INITIATION_QUICK.md \
        deploy_fix_initiation.sh

echo ""
echo "💾 Commit..."
git commit -m "fix: Empêcher initiation si conversation existe déjà

🔧 Problème:
- Bot envoyait message d'initiation après 13+ messages existants
- User disait 'parle moi de toi' → Bot: 'Salut Albert ! Je vis...'
- Incohérence catastrophique

✅ Solution:
- Vérification AVANT création initiation
- _check_existing_messages() compte messages
- Si messages > 0 → Pas d'initiation

Impact:
- User initie → Bot répond normalement (pas d'initiation)
- Bot initie → Cohérent (premier message réel)

Fixes: Initiation après conversation existante"

echo ""
echo "⬆️  Push vers Railway..."
git push origin main

echo ""
echo "✅ DÉPLOYÉ AVEC SUCCÈS !"
echo ""
echo "⏳ Railway va rebuild en ~60 secondes..."
echo ""
echo "🧪 PROCHAINES ÉTAPES :"
echo "  1. Attendre 60s pour rebuild Railway"
echo "  2. Vérifier logs : railway logs --tail"
echo "  3. Tester dans Flutter : Nouveau match → Envoyer 'Salut'"
echo "  4. Vérifier : Bot répond normalement (PAS d'initiation)"
echo ""
echo "📊 Logs attendus :"
echo "  '🚫 Match xxx a déjà 1 message(s), pas d'initiation'"
echo ""
