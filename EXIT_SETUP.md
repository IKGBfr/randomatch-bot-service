# Configuration Cron Job Railway

## Task: Unmatch automatique après exit bot

### 1. Ajouter service dans Railway

Dans Railway Dashboard → New Service:

```
Service name: bot-unmatch-cron
Command: python -m app.scheduled_tasks
Schedule: */10 * * * *  (toutes les 10 minutes)
```

### 2. Variables d'environnement

Mêmes variables que le worker:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `POSTGRES_CONNECTION_STRING`

### 3. Alternative simple: Appel manuel

Si pas de cron Railway disponible, appeler manuellement:

```bash
cd /Users/anthony/Projects/randomatch-bot-service
python -m app.scheduled_tasks
```

### 4. Comment ça marche

1. Bot envoie messages normalement
2. Après 15-30 messages → Bot dit qu'il a rencontré quelqu'un
3. Bot_exit_reason + bot_exited_at enregistrés
4. Cron job check toutes les 10min
5. Si bot_exited_at > 30min → Unmatch automatique

### 5. Logs à surveiller

Dans worker:
```
🚪 Phase 7: Vérification exit...
   ⚠️ Bot doit quitter: limit_reached
📤 Envoi séquence exit (2 messages)...
   ✅ Exit message 1 envoyé
   ✅ Exit message 2 envoyé
   🎯 Bot a quitté la conversation
```

Dans cron:
```
🔍 Recherche conversations à unmatch...
   📋 3 match(s) à unmatch
   🔄 Unmatch abc123... (raison: limit_reached)
      ✅ Unmatch créé
```

### 6. Configuration personnalisée

Dans `.env`:
```bash
# Exit Manager Config
BOT_MIN_MESSAGES=15   # Min avant exit possible
BOT_MAX_MESSAGES=30   # Max absolu
BOT_EXIT_CHANCE=0.05  # 5% chance random par message
```

### 7. Test local

```bash
# Terminal 1: Worker
python -m app.main_worker

# Terminal 2: Envoyer 20+ messages avec bot

# Terminal 3: Vérifier exit
python -m app.scheduled_tasks
```
