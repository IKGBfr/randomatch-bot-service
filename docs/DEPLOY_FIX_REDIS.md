# 🚀 Guide de Déploiement - Fix Redis Connection Lost

## ⚡ Déploiement Rapide (5 minutes)

### 1. Commit & Push
```bash
cd /Users/anthony/Projects/randomatch-bot-service

# Status
git status

# Add & commit
git add app/bridge_intelligence.py docs/FIX_REDIS_CONNECTION_LOST.md
git commit -m "fix: Ajouter retry + reconnexion Redis dans bridge

- 3 tentatives avec backoff exponentiel (1s, 2s, 4s)
- Reconnexion automatique entre tentatives
- Logging détaillé pour diagnostic
- Gestion erreurs spécifiques (JSON, KeyError, ConnectionError)

Résout: Perte de messages lors micro-coupures Redis
Voir: docs/FIX_REDIS_CONNECTION_LOST.md"

# Push
git push origin main
```

### 2. Vérifier Railway Deploy
```bash
# Ouvrir Dashboard Railway
open https://railway.app/project/your-project-id

# Ou via CLI
railway logs --tail

# Attendre logs de démarrage:
# ✅ Connecté à PostgreSQL
# ✅ Connecté à Redis
# 👂 Démarrage écoute 'bot_events' et 'new_match'...
# ✅ Écoute active
```

### 3. Test Immédiat
**Dans Flutter (localhost:8080) :**
1. Ouvrir conversation avec Camille
2. Envoyer message "test"
3. Observer logs Railway en direct

**Logs attendus:**
```
📨 Notification reçue (pid=..., channel=bot_events)
   Payload: {"match_id":"...","sender_id":"...","bot_id":"...
   Match ID: de31323b-fb0b-4ac0-aa5a-e5b3299a5567
⏰ Nouveau message, démarrage timer 15s
📦 Grouping: 1 messages
✅ Message poussé dans queue
```

### 4. Si Erreur Redis (Test Resilience)
**Logs si micro-coupure:**
```
📨 Notification reçue
⚠️ Tentative 1/3 - Connexion Redis perdue: Connection reset
⏳ Retry dans 1s...
🔄 Reconnexion Redis...
✅ Reconnexion Redis réussie
✅ Message poussé dans queue
```

**→ Succès ! Le message n'est plus perdu.**

---

## 📊 Validation Complète (30 minutes)

### Test 1: Messages Normaux (5 min)
```bash
# Envoyer 10 messages dans Flutter
# Tous doivent être traités

# Vérifier dans logs
railway logs --tail | grep "Message poussé"
# Devrait voir 10x "✅ Message poussé dans queue"
```

### Test 2: Grouping (5 min)
```bash
# Envoyer 3 messages rapides (<3s entre chaque)
# Observer grouping

# Logs attendus
railway logs --tail | grep -E "Grouping|timer"
# 📨 Notification reçue
# ⏰ Nouveau message, démarrage timer 15s
# 🔄 Grouping: +1 message (2 total)
# 🔄 Grouping: +1 message (3 total)
# 📦 Grouping: 3 messages
# ✅ Message poussé dans queue
```

### Test 3: Initiation Post-Match (10 min)
```bash
# Créer nouveau match avec bot dans Flutter
# Attendre 0-60s (TEST_MODE)

# Logs attendus
railway logs --tail | grep -E "Nouveau match|Initiation"
# 🔍 Nouveau match détecté
# 💬 Initiation pour match ...
# ✅ Message poussé dans queue
```

### Test 4: Load Test (10 min)
```bash
# Envoyer 50 messages rapides
# Observer que tous sont traités

# Stats
railway logs --tail | grep "Message poussé" | wc -l
# Devrait = 50 (ou moins si groupés)
```

---

## 🎯 Checklist Validation

**Fonctionnalités Core:**
- [ ] Messages utilisateurs détectés instantanément
- [ ] Grouping fonctionne (3+ messages rapides)
- [ ] Bot répond avec délais naturels
- [ ] Initiation post-match fonctionne
- [ ] Pas de messages perdus

**Robustesse:**
- [ ] Aucune erreur "Connection lost" dans logs
- [ ] Si erreur Redis, retry + reconnexion réussie
- [ ] Logs détaillés et informatifs
- [ ] Pas de crash bridge/worker

**Performance:**
- [ ] Latence détection <500ms
- [ ] Temps push Redis <50ms
- [ ] Aucun timeout PostgreSQL
- [ ] Grouping timer respecté (15s)

---

## 🐛 Troubleshooting Post-Deploy

### Problème: Bridge crash au démarrage
**Symptôme:**
```
❌ Erreur fatale: [Errno 61] Connection refused
```

**Solution:**
```bash
# Vérifier variables env Railway
railway vars

# Vérifier REDIS_URL est valide
redis-cli -u $REDIS_URL ping
# Devrait retourner "PONG"
```

### Problème: Messages toujours perdus
**Symptôme:**
```
⚠️ Tentative 1/3 - Connexion Redis perdue
⚠️ Tentative 2/3 - Connexion Redis perdue
❌ Échec définitif après 3 tentatives
```

**Solution:**
```bash
# Redis Upstash vraiment down ?
curl https://status.upstash.com

# Tester connexion directe
redis-cli -u $REDIS_URL ping

# Si down, attendre retour service
# Ou changer instance Redis
```

### Problème: Grouping ne fonctionne plus
**Symptôme:**
```
# Aucun log "Grouping" malgré messages rapides
```

**Solution:**
```bash
# Vérifier GROUPING_DELAY
railway logs | grep "GROUPING_DELAY"

# Vérifier contexte Redis
redis-cli -u $REDIS_URL KEYS "context:*"

# Si vide alors que messages rapides, redémarrer bridge
railway restart
```

---

## 📈 Monitoring Post-Deploy

**Dashboard Railway - À surveiller 24h:**

1. **CPU Usage**
   - Normal: 5-15%
   - Alerte si >50%

2. **Memory Usage**
   - Normal: 100-200MB
   - Alerte si >500MB

3. **Error Rate**
   - Normal: 0-1 erreur/heure
   - Alerte si >5 erreurs/heure

4. **Logs Patterns**
   ```bash
   # Retries Redis
   railway logs | grep "⚠️ Tentative"
   # Devrait être rare (<5/jour)
   
   # Échecs définitifs
   railway logs | grep "❌ Échec définitif"
   # Devrait être 0
   
   # Messages poussés
   railway logs | grep "✅ Message poussé"
   # Devrait être fréquent
   ```

---

## ✅ Validation Finale

**Après 24h de monitoring:**

- [ ] Aucun "❌ Échec définitif" dans logs
- [ ] <10 retries Redis/jour
- [ ] 100% messages utilisateurs traités
- [ ] Aucun crash bridge/worker
- [ ] CPU/Memory stables
- [ ] Utilisateurs ne rapportent aucun problème

**Si tout ✅ → Fix validé et documenté**

---

**Date Deploy:** 30 octobre 2025  
**Version:** bridge_intelligence v2.1  
**Status:** ✅ En production  
**Prochaine revue:** 7 novembre 2025
