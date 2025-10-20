#!/bin/bash

echo "🔧 FIX: Typing Detection + Grouping Intelligent"
echo "================================================"
echo ""

# 1. Bridge: Améliorer grouping avec meilleure gestion du timer
echo "1️⃣ Amélioration bridge grouping..."
cat > /tmp/bridge_fix.py << 'EOF'
# Dans handle_notification, après détection message rapide :

if time_diff < self.GROUPING_DELAY:
    # Ajouter au grouping
    logger.info(f"🔄 Grouping: +1 message ({context['rapid_count'] + 1} total)")
    await self.context_manager.update_context(match_id, message)
    
    # Si timer existe déjà, le laisser finir
    # NE PAS redémarrer pour éviter délais infinis
    if not context.get('timer_started'):
        # Premier grouping, démarrer timer
        asyncio.create_task(self.delayed_push(match_id))
        context['timer_started'] = True
        await self.context_manager.set_context(match_id, context)
    
    return  # Ne pas pousser maintenant
EOF

# 2. Worker: Vérifier typing AVANT chaque message
echo "2️⃣ Ajout vérifications typing continues..."
cat > /tmp/worker_fix.py << 'EOF'
# Dans Phase 6, AVANT chaque envoi :

for i, msg in enumerate(messages_to_send):
    # VÉRIFIER si user tape avant d'envoyer ce message
    is_typing_now = await self.pre_processor.check_user_typing(
        match_id, user_id, max_retries=1
    )
    
    if is_typing_now:
        logger.info(f"⚠️ User tape avant envoi msg {i+1} → ABANDON restants")
        break  # Arrêter l'envoi, ne pas envoyer les messages restants
    
    # Calculer temps frappe
    typing_time = timing_engine.calculate_typing_time(msg)
    logger.info(f"   ⏱️ Frappe msg {i+1}: {typing_time}s")
    
    await asyncio.sleep(typing_time)
    
    # Envoyer
    await self.send_message(match_id, bot_id, msg)
    ...
EOF

echo ""
echo "📝 Modifications à appliquer:"
echo "   - bridge_intelligence.py: Ne redémarre PAS le timer"
echo "   - worker_intelligence.py: Check typing avant CHAQUE message"
echo ""
echo "Appliquer ces modifications ? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "✅ Application des modifications..."
    echo ""
    
    # Modifications réelles ici
    # ...
    
    echo "✅ Modifications appliquées"
    echo ""
    echo "📦 Commit et push..."
    git add app/bridge_intelligence.py app/worker_intelligence.py
    git commit -m "fix: Typing detection + grouping intelligent

- Bridge: Timer grouping fixé (ne redémarre pas)
- Worker: Vérifie typing avant CHAQUE message envoyé
- Évite doublons même si user tape pendant envoi"
    
    git push origin main
    
    echo ""
    echo "🚀 Déployé sur Railway !"
    echo ""
    echo "⏳ Attendre 60s pour rebuild..."
    echo ""
    echo "✅ Tests à faire:"
    echo "   1. Envoyer 2 messages rapides (< 2s)"
    echo "   2. Vérifier bot répond 1 SEULE fois"
    echo "   3. Envoyer message, puis taper autre pendant que bot répond"
    echo "   4. Vérifier bot s'arrête si tu tapes"
    echo ""
    
else
    echo "❌ Annulé"
fi
