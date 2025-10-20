# 🤖 RandoMatch Bot Service

> Service Python autonome pour gérer les conversations IA dans RandoMatch

Bot conversationnel qui répond comme un humain dans l'app de dating pour randonneurs RandoMatch. Architecture professionnelle avec Railway + Redis + PostgreSQL NOTIFY. 

---

## 🏗️ Architecture

```
Flutter Web (Vercel)
       ↕️
Supabase PostgreSQL + Realtime
       ↕️ PostgreSQL NOTIFY
Bridge Python (Railway) ← Always running
       ↕️
Redis Queue (Upstash)
       ↕️
Worker Python (Railway) ← Processes messages
       ↕️
OpenRouter API (Grok 4 Fast)
```

**Principes :**
- Réaction instantanée via PostgreSQL NOTIFY (<100ms)
- Queue Redis pour fiabilité (messages en sécurité)
- Pas de timeout (vs 60s edge functions)
- Retry automatique si API échoue
- Comportements humains : timing naturel, typing indicator, messages multiples

---

## 🚀 Quick Start

### Prérequis
- Python 3.11+
- Compte Railway.app
- Compte Upstash.com (Redis)
- Credentials Supabase

### Installation Locale

```bash
# Clone
git clone https://github.com/ton-username/randomatch-bot-service.git
cd randomatch-bot-service

# Virtual env
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dépendances
pip install -r requirements.txt

# Variables d'environnement
cp .env.example .env
# Éditer .env avec tes credentials
```

### Déploiement Railway

1. Push sur GitHub
2. Railway.app → New Project → Deploy from GitHub
3. Sélectionner ce repo
4. Ajouter variables d'environnement (voir ci-dessous)
5. Deploy automatique ! ✨

---

## 🔧 Configuration

### Variables d'Environnement

```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbG...  # Service role key
POSTGRES_CONNECTION_STRING=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres

# Redis (Upstash)
REDIS_URL=redis://default:password@xxx.upstash.io:6379

# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-...

# Bot Config
BOT_ID=uuid-du-bot-camille
TYPING_SPEED_CPS=3.5  # Caractères par seconde
MIN_THINKING_DELAY=3  # Secondes
MAX_THINKING_DELAY=15
```

---

## 📁 Structure du Projet

```
randomatch-bot-service/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration env vars
│   ├── bridge.py           # Écoute PostgreSQL NOTIFY
│   ├── worker.py           # Traite messages de Redis
│   ├── generator.py        # Appelle OpenRouter/Grok
│   ├── supabase_client.py  # INSERT messages
│   └── timing.py           # Calculs délais humains
├── Procfile                # Définit processus Railway
├── requirements.txt        # Dépendances Python
├── .env.example            # Template variables
├── .gitignore
└── README.md
```

---

## 🎯 Fonctionnement

### 1. Détection Message (Bridge)

```python
# app/bridge.py
# Écoute PostgreSQL NOTIFY 24/7
await pg_conn.add_listener('bot_events', handle_notification)

# Quand message arrive
async def handle_notification(payload):
    await redis_client.rpush('bot_messages', payload)
```

### 2. Traitement (Worker)

```python
# app/worker.py
while True:
    # Attend message (bloquant)
    message = redis.blpop('bot_messages', timeout=1)
    
    if message:
        # 1. Calculer délai réflexion
        delay = calculate_thinking_delay(message)
        await sleep(delay)
        
        # 2. Activer typing
        activate_typing(bot_id, match_id)
        
        # 3. Générer réponse
        response = generate_response(message)
        
        # 4. Simuler frappe
        typing_time = calculate_typing_time(response)
        await sleep(typing_time)
        
        # 5. Envoyer
        send_message(match_id, bot_id, response)
        deactivate_typing(bot_id, match_id)
```

### 3. Génération IA

```python
# app/generator.py
client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY
)

response = client.chat.completions.create(
    model="x-ai/grok-4-fast",
    messages=[
        {"role": "system", "content": bot_personality},
        {"role": "user", "content": user_message}
    ],
    temperature=0.8
)
```

---

## 🧪 Tests

```bash
# Test local bridge
python -m app.bridge

# Test local worker
python -m app.worker

# Test génération
python -m app.generator
```

---

## 📊 Monitoring

### Logs Railway
```bash
railway logs --tail
```

### Vérifier Redis
```bash
redis-cli -h xxx.upstash.io -p 6379 -a password
LLEN bot_messages  # Nombre messages en attente
```

### Métriques
- Temps de réponse moyen
- Taux d'erreur API
- Messages traités/heure

---

## 🐛 Debugging

### Bot ne répond pas

1. Vérifier logs Railway : `railway logs --tail`
2. Vérifier trigger SQL actif : `SELECT * FROM pg_trigger WHERE tgname = 'on_message_notify_bot'`
3. Vérifier Redis : messages dans queue ?
4. Vérifier credentials OpenRouter

### Timing bizarre

1. Ajuster `MIN_THINKING_DELAY` et `MAX_THINKING_DELAY`
2. Ajuster `TYPING_SPEED_CPS` (3-4 réaliste)
3. Vérifier logs : délais calculés

### Réponses en double

1. Vérifier un seul worker actif
2. Vérifier Redis BLPOP (pas RPOP qui ne retire pas)
3. Logs : même message traité 2x ?

### Grok erreur

```bash
# Vérifier API key
echo $OPENROUTER_API_KEY

# Test direct
python -c "
from openai import OpenAI
client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key='$OPENROUTER_API_KEY')
print(client.chat.completions.create(model='x-ai/grok-4-fast', messages=[{'role':'user','content':'test'}]))
"
```

---

## 🚀 Roadmap

- [x] Phase 1 : Setup Railway basique
- [x] Phase 2 : Bridge PostgreSQL → Redis
- [x] Phase 3 : Bot répond (basique)
- [x] Phase 4 : Timing humain + typing
- [ ] Phase 5 : Celery pour robustesse
- [ ] Phase 5 : Grouping intelligent
- [ ] Phase 5 : Mémoire conversationnelle
- [ ] Phase 5 : API monitoring FastAPI

---

## 📚 Documentation

- [Guide Complet](./docs/GUIDE.md)
- [Décisions Architecturales](./docs/DECISIONS.md)
- [Troubleshooting](./docs/TROUBLESHOOTING.md)

---

## 🤝 Contribution

Ce repo est privé pour le projet RandoMatch. Pour questions :
- GitHub Issues
- Email : [email]

---

## 📄 License

Propriétaire - RandoMatch © 2025

---

**Status :** 🟢 Production  
**Version :** 1.0.0  
**Dernière mise à jour :** 18 octobre 2025
