#!/bin/bash

echo "🔧 DÉPLOIEMENT FIX INITIATION EN DOUBLE"
echo "========================================="
echo ""
echo "PROBLÈME RÉSOLU:"
echo "- Bot envoyait 'Salut Albert' en plein milieu de conversation"
echo ""
echo "CAUSE:"
echo "- Match monitor ne vérifiait que les messages de l'USER"
echo "- Si bot avait initié, il ne détectait pas la conversation existante"
echo ""
echo "FIX:"
echo "- Vérifie maintenant TOUS les messages du match (bot OU user)"
echo "- Annule initiation si conversation existe déjà"
echo ""
echo "FICHIERS MODIFIÉS:"
echo "- app/match_monitor.py : Vérification messages améliorée"
echo ""
read -p "Déployer sur Railway ? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📦 Commit des changements..."
    git add app/match_monitor.py
    git commit -m "fix(initiation): Vérifie tous les messages avant initiation

- Problème: Bot envoyait 'Salut User' en plein conversation
- Cause: Ne vérifiait que les messages de l'user
- Fix: Vérifie maintenant TOUS les messages (bot OU user)
- Impact: Annule initiation si conversation existe déjà"
    
    echo ""
    echo "🚀 Push vers Railway..."
    git push origin main
    
    echo ""
    echo "✅ DÉPLOYÉ !"
    echo ""
    echo "⏱️  Attendre 60s pour rebuild Railway..."
    echo ""
    echo "🧪 TESTS À FAIRE:"
    echo "1. Matcher avec bot"
    echo "2. Envoyer message avant que bot initie"
    echo "3. Vérifier que bot NE RENVOIE PAS 'Salut User'"
    echo ""
    echo "📊 VÉRIFIER LOGS:"
    echo "railway logs --service worker --tail"
    echo ""
    echo "Chercher:"
    echo "🚫 Initiation xxx annulée (conversation existe déjà)"
    echo ""
else
    echo ""
    echo "❌ Déploiement annulé"
fi
