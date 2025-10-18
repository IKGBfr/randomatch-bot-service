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
OpenRouter API (Grok 2)
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
# Virtual env
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec tes credentials

# Test
python -m app.test_config
```

### Déploiement Railway

1. Push sur GitHub
2. Railway.app → New Project → Deploy from GitHub
3. Sélectionner ce repo
4. Ajouter variables d'environnement (voir `.env.example`)
5. Deploy automatique ! ✨

---

## 🔧 Configuration

### Variables d'Environnement Requises

Voir `.env.example` pour la liste complète.

**Important :** 
- `BOT_ID` : UUID du profil bot Camille (récupérer depuis Supabase)
- `OPENROUTER_API_KEY` : Clé API OpenRouter
- `REDIS_URL` : URL Redis depuis Upstash

---

## 📁 Structure du Projet

```
randomatch-bot-service/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration env vars
│   └── test_config.py      # Script de test Phase 1
├── Procfile                # Définit processus Railway
├── requirements.txt        # Dépendances Python
├── .env.example            # Template variables
├── .gitignore
└── README.md
```

---

## 🧪 Tests

```bash
# Test configuration et OpenRouter
python -m app.test_config
```

---

## 📊 Roadmap

- [x] Phase 0 : Préparation comptes
- [x] Phase 1 : Setup Railway basique + test config
- [ ] Phase 2 : Bridge PostgreSQL → Redis
- [ ] Phase 3 : Bot répond (basique)
- [ ] Phase 4 : Timing humain + typing
- [ ] Phase 5 : Celery pour robustesse

---

## 📚 Documentation

- [Guide Complet](./docs/GUIDE.md)
- [Décisions Architecturales](./docs/DECISIONS.md)

---

**Status :** 🟡 Phase 1 - Setup  
**Version :** 1.0.0  
**Dernière mise à jour :** 18 octobre 2025
