#!/bin/bash

echo "🔧 FIX: Typing Detection + Grouping Intelligent"
echo "================================================"
echo ""
echo "✅ Modifications appliquées:"
echo "   - bridge_intelligence.py: Timer grouping ne redémarre plus"
echo "   - worker_intelligence.py: Check typing avant CHAQUE message"
echo ""
echo "📝 Changements:"
echo ""
echo "1️⃣ BRIDGE (grouping messages rapides):"
echo "   - Démarre timer 8s au premier message groupé"
echo "   - NE redémarre PAS le timer sur messages suivants"
echo "   - Évite délais infinis si user tape lentement"
echo ""
echo "2️⃣ WORKER (envoi messages):"
echo "   - Vérifie si user tape AVANT d'envoyer chaque message"
echo "   - Si user tape → abandonne messages restants"
echo "   - Évite envoyer pendant que user écrit"
echo ""
echo "🎯 Résultat attendu:"
echo "   ✅ 2 messages rapides → Bot répond 1 SEULE fois"
echo "   ✅ User tape pendant bot → Bot s'arrête"
echo "   ✅ Pas de contradictions"
echo "   ✅ Pas de doublons"
echo ""
echo "📦 Déployer maintenant ? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "📦 Commit..."
    git add app/bridge_intelligence.py app/worker_intelligence.py
    git commit -m "fix: Typing detection + grouping intelligent

- Bridge: Timer grouping fixé (ne redémarre plus)
  * Démarré une seule fois au 1er message groupé
  * Évite délais infinis si user tape lentement
  
- Worker: Vérifie typing avant CHAQUE message
  * Check avant d'envoyer msg 1, msg 2, msg 3...
  * Abandonne messages restants si user tape
  
Résultat: Évite doublons même si user envoie 2-3 messages rapides"
    
    echo ""
    echo "🚀 Push vers Railway..."
    git push origin main
    
    echo ""
    echo "✅ Déployé !"
    echo ""
    echo "⏳ Attendre 60s pour rebuild Railway..."
    sleep 60
    
    echo ""
    echo "📊 Vérifier déploiement:"
    echo "   railway logs --service bridge --tail"
    echo "   railway logs --service worker --tail"
    echo ""
    echo "🧪 Tests à faire:"
    echo "   1. Envoyer 'Salut' puis 'ça va ?' rapidement (<2s)"
    echo "      → Bot doit répondre 1 SEULE fois"
    echo ""
    echo "   2. Envoyer 'Salut', puis taper (sans envoyer)"
    echo "      → Bot doit attendre que tu aies fini"
    echo ""
    echo "   3. Bot commence à taper, envoyer nouveau message"
    echo "      → Bot doit s'arrêter et reprendre"
    echo ""
    
else
    echo ""
    echo "❌ Annulé - Les modifications restent locales"
    echo ""
    echo "Pour déployer plus tard:"
    echo "   ./deploy_typing_fix.sh"
    echo ""
fi
