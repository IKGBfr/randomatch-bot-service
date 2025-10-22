#!/bin/bash
# Script pour vider la queue Redis bot_messages

echo "🧹 Vidage de la queue Redis 'bot_messages'..."

# Se connecter à Railway et exécuter la commande Redis
railway run redis-cli -h ${REDIS_URL} DEL bot_messages

echo "✅ Queue vidée !"
echo "📊 Vérification : $(railway run redis-cli -h ${REDIS_URL} LLEN bot_messages) messages restants"
