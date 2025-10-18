# 🚀 Guide de Déploiement Railway - Phase 2

## 📋 Prérequis
- ✅ Code pushé sur GitHub
- ✅ Compte Railway créé
- ✅ Trigger SQL créé dans Supabase
- ✅ Redis Upstash configuré

## 🎯 Étapes de Déploiement

### 1. Connecter le Repo à Railway

1. Va sur https://railway.app/new
2. Sélectionne "Deploy from GitHub repo"
3. Choisis `IKGBfr/randomatch-bot-service`
4. Railway détecte automatiquement Python

### 2. Configurer les Variables d'Environnement

Dans Railway → ton projet → Variables :

```env
SUPABASE_URL=https://mqshuuqdxerisucqjtuh.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1xc2h1dXFkeGVyaXN1Y3FqdHVoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcyNzI1MDY2OSwiZXhwIjoyMDQyODI2NjY5fQ.2sRF4IBMqPtZ60v-Y6uy7G1LvLGDOUKJRSyuiW52WOU

POSTGRES_CONNECTION_STRING=postgresql://postgres:ANuNgpYP6_E2FnX@db.mqshuuqdxerisucqjtuh.supabase.co:5432/postgres

REDIS_URL=rediss://default:AT10AAIncDJiNjMxYzRlYzUxYTY0MzNhYmRiNjQ3Zjg5Njg0NGE1ZnAyMTU3MzI@perfect-warthog-15732.upstash.io:6379

OPENROUTER_API_KEY=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
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=x-ai/grok-4-fast

TYPING_SPEED_CPS=3.5
MIN_THINKING_DELAY=3
MAX_THINKING_DELAY=15

ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 3. Déployer

Railway va automatiquement :
- Installer les dépendances (`requirements.txt`)
- Lancer le service défini dans `Procfile` (bridge)

### 4. Vérifier les Logs

Dans Railway → ton projet → Deployments → Logs :

Tu devrais voir :
```
🚀 RANDOMATCH BOT SERVICE - BRIDGE POSTGRESQL
🔌 Connexion à PostgreSQL...
✅ Connecté à PostgreSQL
🔌 Connexion à Redis...
✅ Connecté à Redis
👂 Démarrage écoute canal 'bot_events'...
✅ Écoute active sur 'bot_events'
⏳ En attente de notifications...
```

### 5. Tester

Envoie un message dans Flutter à Camille ou Paul.

Dans les logs Railway, tu devrais voir :
```
📨 Notification reçue sur canal 'bot_events'
📦 Payload: {'match_id': 'xxx', 'bot_id': 'yyy', ...}
✅ Message poussé dans Redis queue 'bot_messages'
   Bot: xxx
   Match: yyy
```

## ✅ Phase 2 Terminée !

Une fois que tu vois les notifications dans les logs Railway, Phase 2 est **validée** ! 🎉

Le bridge fonctionne et pousse les messages dans Redis.

## 🚀 Prochaine Étape : Phase 3

Phase 3 = Worker qui prend les messages de Redis et génère les réponses avec Grok !

---

**Note :** La connexion PostgreSQL fonctionne sur Railway mais pas en local à cause des restrictions réseau de ton Mac (IPv6, DNS, etc.). C'est normal et attendu ! 👍
