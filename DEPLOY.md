# 🚀 Déploiement Rapide - RandoMatch Bot Service

## ⚡ Quick Start (5 minutes)

### Option 1 : Script Automatique (Recommandé)

```bash
# 1. Vérifier que tout est prêt
python3 verify_ready.py

# 2. Déployer automatiquement
chmod +x deploy.sh
./deploy.sh
```

### Option 2 : Manuel

```bash
# 1. Vérifier
python3 verify_ready.py

# 2. Commit & Push
git add .
git commit -m "feat: Phase 1-2 complete - Bot Intelligence"
git push origin main

# 3. Railway déploiera automatiquement
```

---

## 📋 Checklist Rapide

Avant de déployer, assure-toi d'avoir :

- [x] ✅ Compte Railway créé et projet configuré
- [x] ✅ Variables env Railway configurées :
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_KEY`
  - `POSTGRES_CONNECTION_STRING`
  - `REDIS_URL` (Upstash)
  - `OPENROUTER_API_KEY`
- [x] ✅ Trigger SQL `on_message_notify_bot` créé dans Supabase
- [x] ✅ Au moins 1 bot profile actif dans Supabase

---

## 🎯 Configuration Railway

### Étape 1 : Créer le Projet

1. Va sur [railway.app/new](https://railway.app/new)
2. "Deploy from GitHub repo"
3. Sélectionne `randomatch-bot-service`
4. Railway détecte automatiquement :
   - `Procfile` → 2 services (bridge + worker)
   - `requirements.txt` → Python
   - Build et deploy automatiques

### Étape 2 : Variables d'Environnement

Dans Railway Dashboard → Settings → Variables, ajoute :

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOi...
POSTGRES_CONNECTION_STRING=postgresql://postgres:password@db.xxxx.supabase.co:5432/postgres
REDIS_URL=rediss://default:password@xxxx.upstash.io:6379
OPENROUTER_API_KEY=sk-or-v1-xxxx
OPENROUTER_MODEL=x-ai/grok-4-fast
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Étape 3 : Premier Deploy

Railway déploie automatiquement après le push Git.

**Temps de build :** 2-3 minutes

---

## 📊 Vérification Post-Déploiement

### Logs Railway

```bash
# Installer Railway CLI
npm i -g @railway/cli

# Login
railway login

# Lier projet
railway link

# Voir logs
railway logs --tail
```

**Logs attendus :**

```
[bridge] ✅ Connecté au canal bot_events
[bridge] 👂 Écoute des notifications...

[worker] ✅ Redis connecté
[worker] 👂 En attente de messages...
```

### Test dans Flutter

1. Match avec bot (Camille ou Paul)
2. Envoie "Salut !"
3. Observe :
   - Typing indicator après 3-5s
   - Bot "tape" quelques secondes
   - Réponse naturelle

---

## 🐛 Troubleshooting

### Problème : Build échoue

**Solution :**
1. Vérifier `requirements.txt` correct
2. Vérifier logs Railway build
3. Python 3.11+ spécifié

### Problème : Bridge ne démarre pas

**Solution :**
1. Vérifier `POSTGRES_CONNECTION_STRING`
2. Format : `postgresql://postgres:pwd@db.xxx.supabase.co:5432/postgres`
3. Port 5432 (pas 6543 pour LISTEN/NOTIFY)

### Problème : Worker ne reçoit rien

**Solution :**
1. Vérifier `REDIS_URL` correct
2. Tester : `redis-cli -u $REDIS_URL ping`
3. Vérifier bridge pousse dans Redis

### Problème : Bot ne répond pas

**Solutions :**
1. Vérifier trigger SQL actif : `SELECT * FROM pg_trigger WHERE tgname='on_message_notify_bot'`
2. Vérifier bot_id existe dans bot_profiles
3. Consulter logs Railway pour erreurs

---

## 📞 Support

- **Docs complètes :** `DEPLOY_GUIDE.md`
- **Vérification :** `python3 verify_ready.py`
- **Railway Docs :** [docs.railway.app](https://docs.railway.app)

---

## ✅ Post-Deploy

Une fois déployé avec succès :

1. **Monitoring :**
   - CPU < 50%
   - Memory < 200MB
   - Pas de restarts

2. **Tests :**
   - Message simple ✓
   - Messages rapides (grouping) ✓
   - Question complexe (multi-messages) ✓

3. **Next Steps :**
   - Phase 3 : Prompt Builder avancé
   - Phase 4 : Memory Manager
   - Phase 5 : Features production

---

**Prêt à déployer ? Lance `python3 verify_ready.py` !** 🚀
