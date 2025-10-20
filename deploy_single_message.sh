#!/bin/bash

echo "🚀 Déploiement Fix Messages Uniques"
echo "===================================="
echo ""
echo "📋 Changements:"
echo "  ✅ Split uniquement sur ||| explicite"
echo "  ✅ Instructions anti-contradiction"
echo "  ✅ Par défaut : UN SEUL MESSAGE"
echo ""

read -p "Déployer ? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Annulé"
    exit 1
fi

git add app/worker_intelligence.py app/prompt_builder.py
git commit -m "fix: Un seul message par défaut, anti-contradiction

- Split uniquement sur ||| explicite (pas \n\n auto)
- Instructions: UN SEUL MESSAGE par défaut
- Anti-contradiction explicite dans prompt
- Fix bot qui envoie plusieurs messages incohérents"

git push origin main

echo ""
echo "✅ Déployé ! Attendre 60s..."
echo ""
echo "Test: Bot doit envoyer 1 seul message cohérent"
