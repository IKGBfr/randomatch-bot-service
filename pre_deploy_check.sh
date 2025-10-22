#!/bin/bash

# Script de vérification pré-déploiement
# Vérifie que tout est prêt avant de déployer en production

echo "═══════════════════════════════════════════════════════════"
echo "🔍 VÉRIFICATION PRÉ-DÉPLOIEMENT"
echo "═══════════════════════════════════════════════════════════"
echo ""

ERRORS=0

# Fonction pour afficher une erreur
error() {
    echo "❌ $1"
    ERRORS=$((ERRORS + 1))
}

# Fonction pour afficher un succès
success() {
    echo "✅ $1"
}

# 1. Vérifier le répertoire
echo "📂 Vérification du répertoire..."
if [ -f "app/robust_service.py" ]; then
    success "Répertoire correct"
else
    error "Pas dans le bon répertoire. cd vers randomatch-bot-service"
fi
echo ""

# 2. Vérifier Git
echo "🔧 Vérification Git..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    success "Dépôt Git initialisé"
    
    # Vérifier la remote
    if git remote get-url origin > /dev/null 2>&1; then
        success "Remote GitHub configurée"
    else
        error "Pas de remote GitHub configurée"
    fi
else
    error "Pas un dépôt Git"
fi
echo ""

# 3. Vérifier les fichiers critiques
echo "📄 Vérification des fichiers..."
files=(
    "app/robust_service.py:Service principal robuste"
    "app/bridge_intelligence.py:Bridge PostgreSQL"
    "app/main_worker.py:Worker Redis"
    "app/config.py:Configuration"
    "app/supabase_client.py:Client Supabase"
    "app/redis_client.py:Client Redis"
    "app/openrouter_client.py:Client OpenRouter"
    "Procfile:Configuration Railway"
    "requirements.txt:Dépendances Python"
    ".env:Variables d'environnement"
)

for file_info in "${files[@]}"; do
    IFS=':' read -r file desc <<< "$file_info"
    if [ -f "$file" ]; then
        success "$desc"
    else
        error "$desc manquant ($file)"
    fi
done
echo ""

# 4. Vérifier le Procfile
echo "📋 Vérification du Procfile..."
if grep -q "web: python -m app.robust_service" Procfile; then
    success "Procfile configuré correctement"
else
    error "Procfile incorrect. Devrait contenir: web: python -m app.robust_service"
fi
echo ""

# 5. Vérifier les dépendances
echo "📦 Vérification des dépendances..."
deps=("aiohttp" "asyncpg" "redis" "supabase" "openai")
for dep in "${deps[@]}"; do
    if grep -q "$dep" requirements.txt; then
        success "$dep"
    else
        error "$dep manquant dans requirements.txt"
    fi
done
echo ""

# 6. Vérifier les variables d'environnement
echo "🔑 Vérification des variables d'environnement..."
if [ -f ".env" ]; then
    required_vars=(
        "SUPABASE_URL"
        "SUPABASE_SERVICE_KEY"
        "POSTGRES_CONNECTION_STRING"
        "REDIS_URL"
        "OPENROUTER_API_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if grep -q "^$var=" .env; then
            success "$var"
        else
            error "$var manquant dans .env"
        fi
    done
else
    error "Fichier .env manquant"
fi
echo ""

# 7. Vérifier la syntaxe Python
echo "🐍 Vérification syntaxe Python..."
if command -v python3 &> /dev/null; then
    if python3 -m py_compile app/robust_service.py 2>/dev/null; then
        success "robust_service.py syntaxe OK"
    else
        error "robust_service.py erreur de syntaxe"
    fi
else
    echo "⚠️  Python3 non trouvé, skip"
fi
echo ""

# 8. Résumé
echo "═══════════════════════════════════════════════════════════"
if [ $ERRORS -eq 0 ]; then
    echo "✅ TOUTES LES VÉRIFICATIONS SONT OK"
    echo ""
    echo "🚀 Vous pouvez déployer avec:"
    echo "   ./deploy_production.sh"
    echo ""
    echo "Ou manuellement:"
    echo "   git add ."
    echo "   git commit -m 'Production-ready bot service'"
    echo "   git push origin main"
else
    echo "❌ $ERRORS ERREUR(S) TROUVÉE(S)"
    echo ""
    echo "Corrigez les erreurs ci-dessus avant de déployer."
fi
echo "═══════════════════════════════════════════════════════════"

exit $ERRORS
