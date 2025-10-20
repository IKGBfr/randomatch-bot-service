#!/bin/bash

echo "🚨 FIX URGENT: Keepalive PostgreSQL"
echo "===================================="
echo ""
echo "❌ Problème: Bridge perd connexion LISTEN après quelques minutes"
echo "✅ Solution: Keepalive SELECT 1 toutes les 30s + reconnexion auto"
echo ""
echo "📝 Modification: app/bridge_intelligence.py"
echo "   - Keepalive toutes les 30s"
echo "   - Reconnexion automatique si échec"
echo ""
echo "🚀 Déployer maintenant ? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "📦 Commit urgent..."
    git add app/bridge_intelligence.py
    git commit -m "fix: Keepalive PostgreSQL LISTEN + reconnexion auto

CRITIQUE: Bridge perdait connexion après quelques minutes

- Keepalive SELECT 1 toutes les 30s
- Reconnexion auto si échec keepalive
- Garantit écoute NOTIFY permanente"
    
    echo ""
    echo "🚀 Push Railway..."
    git push origin main
    
    echo ""
    echo "✅ Déployé !"
    echo ""
    echo "⏳ Attendre 60s rebuild..."
    sleep 60
    
    echo ""
    echo "📊 Vérifier logs:"
    echo "   railway logs --service bridge --tail"
    echo ""
    echo "Chercher:"
    echo "   💓 Keepalive PostgreSQL (toutes les 30s)"
    echo "   📨 Notification reçue (sur tes messages)"
    echo ""
    
else
    echo ""
    echo "❌ Annulé"
fi
