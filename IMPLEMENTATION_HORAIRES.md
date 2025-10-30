# 🌙 Guide d'Intégration des Horaires de Disponibilité

## ✅ Statut Actuel

**Fichiers créés :**
- ✅ `app/availability_checker.py` - Module de vérification des horaires
- ✅ `app/test_availability.py` - Tests de validation

**Configuration DB :**
- ✅ Horaires configurés dans `bot_profiles`
  - Camille & Paul : 7h30-23h00 (semaine), 8h00-23h30 (weekend)

**À faire :**
- ⏳ Intégrer dans `worker_intelligence.py`
- ⏳ Tester en production

---

## 📝 Étape 1 : Intégrer dans Worker Intelligence

### Modifications à apporter dans `app/worker_intelligence.py`

#### A. Ajouter l'import

```python
# Ligne 27 environ, après les autres imports
from app.availability_checker import get_availability_checker
```

#### B. Ajouter le checker dans __init__

```python
def __init__(self):
    # ... autres attributs existants ...
    
    # 🆕 AVAILABILITY CHECKER
    self.availability_checker = None  # Sera initialisé dans connect_supabase
```

#### C. Initialiser le checker dans connect_supabase

```python
async def connect_supabase(self):
    """Connexion Supabase custom client"""
    logger.info("🔌 Connexion à Supabase...")
    self.supabase = SupabaseClient()
    await self.supabase.connect()
    self.pre_processor = PreProcessor(self.supabase)
    
    # 🆕 Initialiser continuous monitor
    self.continuous_monitor = ContinuousMonitor(self.supabase)
    
    # 🆕 Initialiser unanswered detector
    self.unanswered_detector = UnansweredDetector()
    
    # 🆕 Initialiser availability checker
    self.availability_checker = await get_availability_checker()
    
    logger.info("✅ Connecté à Supabase + Continuous Monitor + Unanswered Detector + Availability Checker")
```

#### D. Vérifier disponibilité avant de traiter le message

Dans la méthode `process_message`, ajouter cette vérification **avant** tout le traitement :

```python
async def process_message(self, payload: dict):
    """Traite un message avec toute l'intelligence conversationnelle"""
    
    match_id = payload.get('match_id')
    bot_id = payload.get('bot_id')
    sender_id = payload.get('sender_id')
    message_content = payload.get('content', '')
    message_id = payload.get('message_id')
    
    # ========================================
    # 🆕 PHASE 0: VÉRIFICATION DISPONIBILITÉ
    # ========================================
    
    is_available, reason = await self.availability_checker.is_bot_available(bot_id)
    
    if not is_available:
        logger.info(f"⏰ Bot {bot_id} indisponible: {reason}")
        
        # Calculer délai jusqu'à la prochaine disponibilité
        delay_seconds = await self.availability_checker.calculate_delay_until_available(bot_id)
        
        if delay_seconds:
            hours = delay_seconds / 3600
            logger.info(f"   ⏰ Sera disponible dans {hours:.1f}h")
            
            # Repousser le message dans la queue avec délai
            await self._requeue_message_with_delay(payload, delay_seconds)
            
            return  # Ne pas traiter maintenant
        else:
            # Pas de restrictions horaires ou erreur
            logger.warning(f"⚠️ Bot indisponible mais pas de délai calculé, traiter quand même")
    
    # ========================================
    # PHASE 1: ACQUISITION LOCK (existant)
    # ========================================
    # ... le reste du code existant continue ici ...
```

#### E. Ajouter la méthode de requeue avec délai

Ajouter cette nouvelle méthode dans la classe `WorkerIntelligence` :

```python
async def _requeue_message_with_delay(self, payload: dict, delay_seconds: int):
    """
    Repousse un message dans la queue Redis pour traitement ultérieur.
    
    Args:
        payload: Le message à traiter plus tard
        delay_seconds: Délai en secondes avant de retraiter
    """
    try:
        # Ajouter un champ pour tracker le requeue
        payload['requeued_at'] = datetime.now().isoformat()
        payload['scheduled_for'] = (datetime.now().timestamp() + delay_seconds)
        
        # Repousser dans la queue
        await self.redis_client.rpush(
            'bot_messages',
            json.dumps(payload)
        )
        
        logger.info(
            f"📬 Message requeued avec délai de {delay_seconds}s "
            f"(~{delay_seconds/3600:.1f}h)"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du requeue: {e}")
```

---

## 🧪 Étape 2 : Tester l'Intégration

### Test 1 : Vérifier la disponibilité actuelle

```bash
cd /path/to/randomatch-bot-service
python -m app.test_availability
```

**Résultat attendu :**
```
🧪 TEST DES HORAIRES DE DISPONIBILITÉ DES BOTS
==================================================================

🤖 Test de disponibilité : Camille
==================================================================
📅 Date: 2025-01-30 Thursday
🕐 Heure: 14:30:00 (Paris)
📆 Type: 💼 Semaine

✅ Camille est DISPONIBLE
   ➤ Peut répondre aux messages

🤖 Test de disponibilité : Paul
==================================================================
📅 Date: 2025-01-30 Thursday
🕐 Heure: 14:30:00 (Paris)
📆 Type: 💼 Semaine

✅ Paul est DISPONIBLE
   ➤ Peut répondre aux messages

📊 RÉSUMÉ DES TESTS
==================================================================
  Camille         : ✅ DISPONIBLE
  Paul            : ✅ DISPONIBLE
```

### Test 2 : Tester hors horaires (simulation)

Pour tester le comportement hors horaires sans attendre la nuit, tu peux temporairement modifier les horaires dans la DB :

```sql
-- Mettre un horaire très court (ex: 14h30-14h35) pour tester
UPDATE bot_profiles 
SET 
    weekday_start_time = '14:30:00',
    weekday_end_time = '14:35:00'
WHERE id = '056fb06d-c6ac-4f52-ad49-df722c0e12e5';  -- Camille

-- Puis relancer le test
-- Tu devrais voir "INDISPONIBLE" si tu es hors de cette plage
```

**Remettre les vrais horaires après :**
```sql
UPDATE bot_profiles 
SET 
    weekday_start_time = '07:30:00',
    weekday_end_time = '23:00:00',
    weekend_start_time = '08:00:00',
    weekend_end_time = '23:30:00'
WHERE id IN (
    '056fb06d-c6ac-4f52-ad49-df722c0e12e5',  -- Camille
    '6fd53f0b-f994-4bd4-84dc-6a19daade13f'   -- Paul
);
```

### Test 3 : Tester avec le worker complet

```bash
# Terminal 1: Bridge
python -m app.bridge_intelligence

# Terminal 2: Worker
python -m app.main_worker

# Terminal 3: Envoyer un message via l'app
# Observer les logs du worker
```

**Logs attendus pendant horaires normaux :**
```
🤖 TRAITEMENT MESSAGE INTELLIGENT
⏰ Bot 056fb... disponible (weekday 14:30 in range 07:30-23:00)
🔒 Phase 1: Acquisition du lock...
   ✅ Lock acquis pour match abc123...
...
```

**Logs attendus hors horaires (ex: 2h du matin) :**
```
🤖 TRAITEMENT MESSAGE INTELLIGENT
⏰ Bot 056fb... indisponible: Bot sleeping (weekday 02:00 outside range 07:30-23:00)
   ⏰ Sera disponible dans 5.5h
📬 Message requeued avec délai de 19800s (~5.5h)
```

---

## ⚠️ Points d'Attention

### 1. Timezone Europe/Paris

Le système utilise **Europe/Paris** partout. Vérifie que :
- Les horaires dans la DB sont bien en heure locale Paris
- Le serveur Railway utilise aussi ce timezone (ou gère correctement les conversions)

### 2. Weekend Detection

- Samedi = 5 (weekday)
- Dimanche = 6 (weekday)
- Les horaires weekend s'appliquent automatiquement

### 3. Cache des Horaires

Le module met en cache les horaires pendant 1 heure pour performance.

Si tu modifies les horaires dans la DB, soit :
- Attendre 1h
- Redémarrer le worker
- Ou vider le cache Redis manuellement

### 4. Messages en Attente

Quand un message est requeued avec délai, il reste dans la queue Redis.

Si le bot se "réveille" entre temps et que d'autres messages arrivent, le message original sera traité avec les nouveaux dans l'ordre de la queue.

---

## 📊 Monitoring Production

### Métriques à Surveiller

1. **Taux de requeue** : Combien de messages sont différés ?
2. **Délais moyens** : Combien de temps les messages attendent-ils ?
3. **Comportement utilisateur** : Les users s'adaptent-ils aux horaires du bot ?

### Queries Utiles

```sql
-- Messages traités par heure (voir distribution)
SELECT 
    DATE_TRUNC('hour', created_at) AS hour,
    COUNT(*) AS messages_count
FROM messages
WHERE sender_id IN (
    '056fb06d-c6ac-4f52-ad49-df722c0e12e5',  -- Camille
    '6fd53f0b-f994-4bd4-84dc-6a19daade13f'   -- Paul
)
AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour DESC;

-- Messages user hors horaires bot
SELECT 
    m.id,
    m.created_at,
    EXTRACT(HOUR FROM m.created_at AT TIME ZONE 'Europe/Paris') AS hour_paris,
    m.content
FROM messages m
JOIN matches ma ON m.match_id = ma.id
WHERE m.sender_id NOT IN (
    '056fb06d-c6ac-4f52-ad49-df722c0e12e5',  -- Camille
    '6fd53f0b-f994-4bd4-84dc-6a19daade13f'   -- Paul
)
AND (
    (EXTRACT(HOUR FROM m.created_at AT TIME ZONE 'Europe/Paris') < 7.5)
    OR (EXTRACT(HOUR FROM m.created_at AT TIME ZONE 'Europe/Paris') >= 23)
)
AND m.created_at >= NOW() - INTERVAL '7 days'
ORDER BY m.created_at DESC
LIMIT 50;
```

---

## 🔄 Rollback Plan

Si problème en production :

### Option 1 : Désactiver Temporairement

Commenter la vérification dans `worker_intelligence.py` :

```python
# # ========================================
# # PHASE 0: VÉRIFICATION DISPONIBILITÉ
# # ========================================
# 
# is_available, reason = await self.availability_checker.is_bot_available(bot_id)
# 
# if not is_available:
#     # ... code requeue ...
#     return
```

Puis redéployer.

### Option 2 : Forcer Disponibilité 24/7

```sql
-- Mettre NULL sur tous les horaires = disponible 24/7
UPDATE bot_profiles
SET 
    weekday_start_time = NULL,
    weekday_end_time = NULL,
    weekend_start_time = NULL,
    weekend_end_time = NULL
WHERE id IN (
    '056fb06d-c6ac-4f52-ad49-df722c0e12e5',
    '6fd53f0b-f994-4bd4-84dc-6a19daade13f'
);
```

---

## ✅ Checklist Finale

Avant de considérer cette feature comme complète :

- [ ] Tests locaux passés avec succès
- [ ] Worker intégré et testé localement
- [ ] Horaires DB configurés correctement
- [ ] Déployé sur Railway
- [ ] Tests en production (pendant et hors horaires)
- [ ] Monitoring mis en place
- [ ] Documentation mise à jour
- [ ] Rollback plan testé

---

## 📚 Ressources

**Fichiers Clés :**
- `app/availability_checker.py` - Module principal
- `app/test_availability.py` - Tests
- `app/worker_intelligence.py` - Intégration worker

**Configuration :**
- Table `bot_profiles` - Horaires
- Variables d'environnement - IDs des bots

**Logs :**
```bash
railway logs --tail --service worker
```

---

**Maintenu par :** Anthony  
**Dernière mise à jour :** 30 octobre 2025  
**Version :** 1.0
