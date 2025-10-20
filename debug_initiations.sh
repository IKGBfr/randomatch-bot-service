#!/bin/bash

echo "🔍 DEBUG INITIATIONS"
echo "===================="
echo ""
echo "Vérifie l'état des initiations dans Supabase"
echo ""

# Commande SQL pour vérifier les initiations
cat << 'EOF'
-- Copier dans Supabase SQL Editor :

-- Initiations en attente
SELECT 
    id,
    match_id,
    status,
    scheduled_for,
    created_at,
    EXTRACT(EPOCH FROM (scheduled_for - NOW())) / 60 as minutes_until_send
FROM bot_initiations
WHERE status = 'pending'
ORDER BY scheduled_for DESC;

-- Initiations envoyées récemment (dernières 24h)
SELECT 
    id,
    match_id,
    status,
    scheduled_for,
    sent_at,
    first_message
FROM bot_initiations
WHERE status = 'sent'
  AND sent_at > NOW() - INTERVAL '24 hours'
ORDER BY sent_at DESC;

-- Initiations annulées récemment (dernières 24h)
SELECT 
    id,
    match_id,
    status,
    scheduled_for,
    updated_at
FROM bot_initiations
WHERE status = 'cancelled'
  AND updated_at > NOW() - INTERVAL '24 hours'
ORDER BY updated_at DESC;

-- Stats globales
SELECT 
    status,
    COUNT(*) as count
FROM bot_initiations
GROUP BY status;
EOF

echo ""
echo "📊 Pour voir stats en temps réel :"
echo "railway logs --service worker --tail | grep -i 'initiation'"
echo ""
