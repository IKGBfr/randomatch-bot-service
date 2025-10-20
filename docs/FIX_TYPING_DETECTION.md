# 🐛 Fix: Typing Detection + Grouping Intelligent

## Problème Identifié

**Symptôme :** Le bot répond plusieurs fois séparément aux messages rapides de l'utilisateur.

**Exemple :**
```
02:47:38 - User: "ok, je suis de Montpellier"
02:47:40 - User: "et toi?" (2s après)
02:48:08 - Bot: "Moi aussi ! C'est sympa..." (30s après message 1)
02:48:27 - Bot: "Moi aussi ! Tu vis..." (19s après réponse 1)
```

**Résultat :** 2 réponses du bot, contradiction ("Moi aussi !" répété)

## Causes Identifiées

### 1. Bridge - Timer Grouping Redémarré
- Le bridge redémarrait le timer à chaque nouveau message
- Si user tapait lentement (8s entre messages), timer infini
- Messages pas groupés correctement

### 2. Worker - Pas de Check Pendant Envoi
- Worker vérifiait typing seulement au début
- Si user tapait pendant envoi message 1, bot envoyait quand même message 2
- Pas de vérification continue

## Solution Implémentée

### 1. Bridge - Timer Unique
```python
# AVANT (problème)
if context.get('timer_task'):
    context['timer_task'].cancel()  # Redémarrait à chaque message
timer_task = asyncio.create_task(self.delayed_push(match_id))

# APRÈS (fixé)
if not context.get('timer_started'):
    # Démarre UNE SEULE FOIS au premier message groupé
    asyncio.create_task(self.delayed_push(match_id))
    context['timer_started'] = True
else:
    # Messages suivants : timer déjà actif
    logger.info("⏰ Timer déjà actif, pas de redémarrage")
```

**Résultat :** Timer de 8s démarre au 1er message, ne redémarre plus.

### 2. Worker - Check Avant Chaque Message
```python
# AVANT (problème)
for i, msg in enumerate(messages_to_send):
    typing_time = timing_engine.calculate_typing_time(msg)
    await asyncio.sleep(typing_time)
    await self.send_message(match_id, bot_id, msg)  # Envoyait sans vérifier

# APRÈS (fixé)
for i, msg in enumerate(messages_to_send):
    # VÉRIFIER si user tape avant d'envoyer
    is_typing_now = await self.pre_processor.check_user_typing(
        match_id, user_id, max_retries=1
    )
    
    if is_typing_now:
        logger.info(f"⚠️ User tape → ABANDON messages restants")
        await self.deactivate_typing(bot_id, match_id)
        break  # Arrêter
    
    typing_time = timing_engine.calculate_typing_time(msg)
    await asyncio.sleep(typing_time)
    await self.send_message(match_id, bot_id, msg)
```

**Résultat :** Worker vérifie avant msg 1, msg 2, msg 3... Arrête si user tape.

## Scénarios de Test

### ✅ Scénario 1 : Messages Rapides
**Input :**
```
00:00:00 - User: "Salut"
00:00:02 - User: "ça va ?" (2s après)
```

**Comportement Attendu :**
1. Bridge reçoit "Salut" → Push immédiat + démarre timer 8s
2. Bridge reçoit "ça va ?" (2s après) → Update contexte (timer déjà actif)
3. Après 8s total → Bridge push groupé `{messages: ["Salut", "ça va ?"]}`
4. Worker reçoit grouping → Génère 1 réponse pour les 2 messages
5. Bot répond **1 SEULE fois** : "Salut ! Ça va bien et toi ?"

### ✅ Scénario 2 : User Tape Pendant Génération
**Input :**
```
00:00:00 - User: "Salut"
00:00:05 - Bot commence traitement (réflexion 5s)
00:00:08 - User commence à taper...
00:00:10 - Bot génère réponse
```

**Comportement Attendu :**
1. Bot vérifie typing avant génération (00:00:10)
2. Détecte user tape
3. Abandonne génération
4. Requeue le message pour traiter plus tard

### ✅ Scénario 3 : User Tape Pendant Envoi
**Input :**
```
00:00:00 - User: "Salut"
00:00:10 - Bot commence envoi msg 1
00:00:12 - User commence à taper...
00:00:14 - Bot veut envoyer msg 2
```

**Comportement Attendu :**
1. Bot envoie msg 1 : "Salut !"
2. **Avant** d'envoyer msg 2 : vérifie typing
3. Détecte user tape
4. Abandonne msg 2
5. Désactive typing
6. Arrête l'envoi

## Résultats Attendus

### Avant le Fix
- ❌ Bot répond plusieurs fois séparément
- ❌ Contradictions ("Moi aussi !" répété)
- ❌ Bot ne s'arrête pas si user tape
- ❌ Messages pas groupés

### Après le Fix
- ✅ Bot répond 1 SEULE fois pour messages rapides
- ✅ Pas de contradictions
- ✅ Bot s'arrête si user tape pendant envoi
- ✅ Messages groupés correctement (delay 8s)

## Métriques de Validation

Après déploiement, surveiller :

```sql
-- Vérifier doublons réduits
SELECT 
  match_id,
  COUNT(*) as responses,
  MAX(created_at) - MIN(created_at) as time_between
FROM messages
WHERE sender_id = '056fb06d-c6ac-4f52-ad49-df722c0e12e5'  -- Camille
GROUP BY match_id, DATE_TRUNC('minute', created_at)
HAVING COUNT(*) > 1
ORDER BY created_at DESC
LIMIT 10;
```

**Métrique :** Doublons en 1 minute doivent être < 5%

## Fichiers Modifiés

- ✅ `app/bridge_intelligence.py` : Timer grouping fixé
- ✅ `app/worker_intelligence.py` : Check typing avant chaque message

## Déploiement

```bash
chmod +x deploy_typing_fix.sh
./deploy_typing_fix.sh
```

## Rollback

Si problème après déploiement :

```bash
git revert HEAD
git push origin main
```

Railway redéploiera automatiquement l'ancienne version.

---

**Date :** 20 octobre 2025  
**Status :** ✅ Prêt à déployer  
**Impact :** Critique (évite doublons et contradictions)
