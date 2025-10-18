# 🤖 RandoMatch Bot Service - Intelligence Conversationnelle

> Service Python autonome avec intelligence conversationnelle avancée

Bot qui répond comme un humain dans RandoMatch. Architecture Railway + Redis + PostgreSQL NOTIFY avec **grouping intelligent**, **détection typing**, et **timing adaptatif**.

---

## 🏗️ Architecture Intelligence

```
Flutter Web (Vercel)
       ↕️
Supabase PostgreSQL + Realtime
       ↕️ PostgreSQL NOTIFY
🧠 Bridge Intelligence (Railway)
   - Grouping messages rapides
   - Context Redis éphémère
       ↕️
Redis Queue (Upstash)
       ↕️
🧠 Worker Intelligence (Railway)
   - Check typing user
   - Load full history
   - Load bot_memory
   - Analyse context
   - Timing adaptatif
       ↕️
OpenRouter API (Grok 4 Fast)
```

**Fonctionnalités Intelligence :**
- ✅ **Grouping** : Messages rapides (<3s) groupés automatiquement
- ✅ **Typing detection** : Attend si user tape encore
- ✅ **Full history** : Charge 50 derniers messages
- ✅ **Memory** : Utilise bot_memory (trust_score, topics, etc.)
- ✅ **Timing adaptatif** : Délais selon urgency/complexity
- ✅ **Multi-messages** : Peut envoyer 2-3 messages naturellement

---

## 🚀 Quick Start

### Installation Locale

```bash
# Virtual env
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec tes credentials

# Test Phase 1
python -m app.test_grouping
```

### Lancer en Local

```bash
# Terminal 1: Bridge Intelligence
python -m app.bridge_intelligence

# Terminal 2: Worker (quand prêt)
python -m app.worker_intelligence
```

---

## 📁 Structure Intelligence

```
randomatch-bot-service/
├── app/
│   ├── __init__.py
│   ├── config.py                  # Config centralisée
│   │
│   ├── bridge_intelligence.py     # 🆕 Bridge avec grouping
│   ├── redis_context.py           # 🆕 Gestion contexte Redis
│   │
│   ├── worker_intelligence.py     # 🆕 Worker intelligent (TODO)
│   ├── pre_processing.py          # 🆕 Check typing, load (TODO)
│   ├── timing_engine.py           # 🆕 Délais adaptatifs (TODO)
│   ├── analysis.py                # 🆕 Analyse message (TODO)
│   ├── prompt_builder.py          # 🆕 Construire prompts (TODO)
│   ├── memory_manager.py          # 🆕 Update mémoire (TODO)
│   │
│   └── test_grouping.py           # Test grouping intelligent
│
├── Procfile                       # Railway config
└── requirements.txt
```

---

## 🧪 Tests Phase 1

### Test Grouping Intelligent

```bash
python -m app.test_grouping
```

**Ce que ça teste :**
1. Message unique → Passe immédiatement
2. 3 messages rapides (<3s) → Groupés après 3s
3. Contexte Redis créé/supprimé correctement

**Vérifications manuelles :**
```bash
# Voir logs bridge
railway logs --tail

# Vérifier Redis
redis-cli -h xxx.upstash.io -p 6379 -a password
LLEN bot_messages      # Voir nombre messages
KEYS context:*         # Voir contextes actifs
```

---

## 📊 Phases d'Implémentation

### ✅ Phase 1 : Bridge Intelligence (TERMINÉ)
- [x] `redis_context.py` - Gestion contexte
- [x] `bridge_intelligence.py` - Grouping intelligent
- [x] `test_grouping.py` - Tests
- [x] `Procfile` - Config Railway

**Fonctionnel :**
- Messages uniques → Queue immédiat
- Messages rapides → Grouping 3s
- Context Redis avec TTL 10s

### 🚧 Phase 2 : Worker Intelligence (EN COURS)
- [ ] `pre_processing.py` - Check typing user
- [ ] `timing_engine.py` - Calculs délais
- [ ] `analysis.py` - Analyse message
- [ ] `worker_intelligence.py` - Orchestration

### ⏳ Phase 3 : Prompt Building
- [ ] `prompt_builder.py` - Construction prompts
- [ ] `context_manager.py` - Gestion historique

### ⏳ Phase 4 : Memory Updates
- [ ] `memory_manager.py` - Updates bot_memory

### ⏳ Phase 5 : Production
- [ ] Tests charge
- [ ] Fine-tuning
- [ ] Monitoring

---

## 🔧 Configuration Avancée

### Redis Context

**Keys utilisées :**
```
context:{match_id}          # Grouping context (TTL 10s)
typing:{match_id}:{user_id} # Typing cache (TTL 5s)
bot_messages                # Queue principale
```

### Grouping

**Paramètres :**
- `GROUPING_DELAY = 3` secondes
- `CONTEXT_TTL = 10` secondes

**Comportement :**
1. Premier message → Passe immédiatement
2. Message suivant < 3s → Ajouté au contexte
3. Timer 3s démarre automatiquement
4. Après 3s → Tous les messages groupés envoyés

---

## 🐛 Debugging

### Bridge pas de réponse

```bash
# 1. Vérifier trigger SQL actif
SELECT * FROM pg_trigger WHERE tgname = 'on_message_notify_bot';

# 2. Vérifier logs Railway
railway logs --tail

# 3. Vérifier Redis
redis-cli LLEN bot_messages
```

### Grouping ne fonctionne pas

```bash
# Vérifier contexte Redis
redis-cli KEYS "context:*"
redis-cli GET "context:uuid-du-match"

# Logs bridge doivent montrer :
# "🔄 Grouping: +1 message"
# "📦 Grouping: 3 messages"
```

---

## 📚 Documentation Détaillée

- [Architecture Complète](../docs/🧠%20Architecture%20Bot%20Intelligent%20Railway%20-%20RandoMatch.md)
- [Guide de Référence](../docs/🗺️%20Guide%20de%20Référence%20-%20Bot%20RandoMatch%20avec%20Railway.md)
- [Décisions Architecturales](../docs/📝%20Log%20des%20Décisions%20-%20Migration%20vers%20Railway.md)

---

## 🚀 Déploiement Railway

```bash
# 1. Commit & Push
git add .
git commit -m "feat: Phase 1 - Bridge Intelligence avec grouping"
git push origin main

# 2. Railway déploie automatiquement

# 3. Vérifier logs
railway logs --tail
```

---

**Status :** 🟢 Phase 1 Complete - Grouping Actif  
**Version :** 2.0.0 - Intelligence  
**Dernière mise à jour :** 18 octobre 2025

---

## 🎯 Next Steps

1. **Tester grouping** avec messages réels
2. **Phase 2** : Worker Intelligence
3. **Deploy production** quand Phase 2-3 complètes
