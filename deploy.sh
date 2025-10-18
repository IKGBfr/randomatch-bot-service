#!/bin/bash
# Script de déploiement automatique pour Railway

echo "========================================================================"
echo "  🚀 DÉPLOIEMENT RAILWAY - RandoMatch Bot Service"
echo "========================================================================"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Étape 1: Vérification pré-déploiement
echo -e "${BLUE}📋 Étape 1/5: Vérification pré-déploiement${NC}"
echo "------------------------------------------------------------------------"
python3 verify_ready.py
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Vérification échouée. Corriger les problèmes avant de continuer.${NC}"
    echo ""
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Vérification réussie${NC}"
echo ""

# Étape 2: Commit message
echo -e "${BLUE}📝 Étape 2/5: Message de commit${NC}"
echo "------------------------------------------------------------------------"
read -p "Message de commit (Enter pour défaut): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="feat: Phase 1-2 complete - Bot Intelligence with grouping and adaptive timing"
fi
echo "Message: $commit_msg"
echo ""

# Étape 3: Git add
echo -e "${BLUE}➕ Étape 3/5: Git add${NC}"
echo "------------------------------------------------------------------------"
git add .
echo -e "${GREEN}✅ Fichiers ajoutés${NC}"
echo ""

# Étape 4: Git commit
echo -e "${BLUE}💾 Étape 4/5: Git commit${NC}"
echo "------------------------------------------------------------------------"
git commit -m "$commit_msg"
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Rien à commiter (fichiers déjà commités)${NC}"
else
    echo -e "${GREEN}✅ Commit créé${NC}"
fi
echo ""

# Étape 5: Git push
echo -e "${BLUE}🚀 Étape 5/5: Git push${NC}"
echo "------------------------------------------------------------------------"
echo "Push vers origin/main..."
git push origin main
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Push échoué${NC}"
    echo ""
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Push réussi${NC}"
echo ""

# Résumé
echo "========================================================================"
echo -e "${GREEN}  🎉 DÉPLOIEMENT TERMINÉ !${NC}"
echo "========================================================================"
echo ""
echo "Prochaines étapes:"
echo "  1. Vérifier que Railway a bien détecté le push"
echo "  2. Attendre le build (2-3 minutes)"
echo "  3. Vérifier que 2 processus tournent (bridge + worker)"
echo "  4. Consulter les logs: railway logs --tail"
echo "  5. Tester avec l'app Flutter"
echo ""
echo "Logs Railway:"
echo "  $ railway logs --tail"
echo ""
echo "Status Railway:"
echo "  https://railway.app/dashboard"
echo ""
