#!/bin/bash

# 🔧 Script de déploiement - Fix Duplication Messages
# Date: 20 octobre 2025

echo "============================================================"
echo "🚀 DÉPLOIEMENT FIX DUPLICATION MESSAGES"
echo "============================================================"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Vérifier que nous sommes sur main
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
    echo -e "${RED}❌ Erreur: Pas sur branche main (actuellement sur $BRANCH)${NC}"
    echo "   Changez vers main avec: git checkout main"
    exit 1
fi

echo -e "${GREEN}✅ Sur branche main${NC}"
echo ""

# Vérifier modifications
echo "📝 Fichiers modifiés:"
echo "---"
git status --short
echo "---"
echo ""

# Confirmer
echo -e "${YELLOW}⚠️  Voulez-vous déployer ces changements ? (y/n)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Déploiement annulé"
    exit 0
fi

echo ""
echo "📦 Ajout des fichiers..."
git add app/bridge_intelligence.py
git add app/worker_intelligence.py
git add FIX_DUPLICATION.md

echo ""
echo "💾 Commit..."
git commit -m "fix: Élimination complète duplication messages

- Bridge: Cooldown 5s après chaque push (évite jobs multiples)
- Worker: Lock par match_id (évite traitement parallèle)
- Résout: 3 réponses pour 1 séquence de messages rapides
- Tests: Messages rapides → 1 seule réponse groupée
- Docs: FIX_DUPLICATION.md complet

Refs: Cas Albert (13:32 - 4 messages → 3 réponses)"

echo ""
echo "🚀 Push vers GitHub..."
git push origin main

echo ""
echo "============================================================"
echo -e "${GREEN}✅ DÉPLOIEMENT TERMINÉ${NC}"
echo "============================================================"
echo ""
echo "📊 Prochaines étapes:"
echo "   1. Railway va auto-déployer (30-60s)"
echo "   2. Vérifier logs: railway logs --tail"
echo "   3. Tester messages rapides dans Flutter"
echo "   4. Chercher dans logs:"
echo "      - '⏰ Cooldown activé pour 5s'"
echo "      - '⏸️ Cooldown actif'"
echo "      - '✅ Messages déjà traités, skip'"
echo ""
echo "🐛 Si problème, rollback:"
echo "   git revert HEAD && git push origin main"
echo ""
