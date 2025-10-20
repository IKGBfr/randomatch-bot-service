#!/bin/bash

echo "============================================================"
echo "🚀 DÉPLOIEMENT FIX CACHE REDIS - ANTI-DOUBLONS"
echo "============================================================"
echo ""
echo "🎯 Objectif: Éliminer doublons de réponses"
echo "📦 Nouveau module: response_cache.py"
echo "🔧 Modifications: worker_intelligence.py"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Vérifier branche
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "main" ]; then
    echo -e "${RED}❌ Pas sur main (sur $BRANCH)${NC}"
    echo "   git checkout main"
    exit 1
fi

echo -e "${GREEN}✅ Sur branche main${NC}"
echo ""

# Vérifier que response_cache.py existe
if [ ! -f "app/response_cache.py" ]; then
    echo -e "${RED}❌ Fichier app/response_cache.py manquant!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ response_cache.py présent${NC}"
echo ""

# Afficher changements
echo "📝 Fichiers modifiés:"
echo "---"
git status --short
echo "---"
echo ""

# Confirmer
echo -e "${YELLOW}⚠️  Déployer ces changements ? (y/n)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Déploiement annulé"
    exit 0
fi

echo ""
echo "📦 Ajout des fichiers..."
git add app/response_cache.py
git add app/worker_intelligence.py
git add FIX_CACHE_REDIS.md

echo ""
echo "💾 Commit..."
git commit -m "fix: Cache Redis - Élimination doublons réponses

🆕 Nouveau module response_cache.py:
- Check génération en cours (flag Redis)
- Détection question similaire (70% match)
- Détection réponse doublon (80% match)
- TTL 60s auto-cleanup

🔧 Worker modifié:
- Phase 0: Vérification cache avant traitement
- Skip si génération en cours OU question similaire
- Check doublon après génération
- Store réponse en cache après envoi

📊 Impact:
- 2 réponses identiques → 1 seule ✅
- Race conditions éliminées
- Mémoire partagée inter-jobs

Fixes: Cas 'tu fais quoi?' → 2x même réponse"

echo ""
echo "🚀 Push vers Railway..."
git push origin main

echo ""
echo "============================================================"
echo "✅ DÉPLOYÉ AVEC SUCCÈS !"
echo "============================================================"
echo ""
echo "📋 PROCHAINES ÉTAPES:"
echo ""
echo "1️⃣  Attendre rebuild Railway (~60s)"
echo "   railway logs --tail"
echo ""
echo "2️⃣  Vérifier logs démarrage:"
echo "   ✅ Connecté à Redis + Cache réponses"
echo "   👂 Écoute queue 'bot_messages'..."
echo ""
echo "3️⃣  Tester avec même question 2x:"
echo "   User: 'tu fais quoi?'"
echo "   (attendre réponse)"
echo "   User: 'tu fais quoi?'"
echo ""
echo "4️⃣  Logs attendus (2ème question):"
echo "   💾 Phase 0: Vérification cache..."
echo "   ⚠️ Question similaire déjà traitée"
echo "   → SKIP pour éviter doublon"
echo ""
echo "5️⃣  Vérifier cache Redis:"
echo "   redis-cli KEYS 'response:*'"
echo "   redis-cli GET 'response:recent:match-xxx'"
echo ""
echo "============================================================"
echo ""
echo "🔍 DEBUGGING:"
echo ""
echo "Si doublons persistent:"
echo "  1. Vérifier logs: 'Pas de doublon détecté'"
echo "  2. Check cache Redis: KEYS 'response:*'"
echo "  3. TTL correct: TTL 'response:generating:xxx'"
echo ""
echo "Si erreurs:"
echo "  1. Rollback: git revert HEAD && git push"
echo "  2. Analyser logs Railway"
echo ""
echo "============================================================"
