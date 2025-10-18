# 🚀 Guide de Déploiement Railway - RandoMatch Bot Service

## 📋 Pré-requis Vérifiés

Avant de déployer, assure-toi d'avoir :

### ✅ Comptes Créés
- [ ] Compte Railway.app actif
- [ ] Compte Upstash.com actif (Redis)
- [ ] Accès Supabase Dashboard
- [ ] Accès OpenRouter API

### ✅ Credentials Disponibles
- [ ] `SUPABASE_URL`
- [ ] `SUPABASE_SERVICE_KEY`
- [ ] `POSTGRES_CONNECTION_STRING`
- [ ] `REDIS_URL` (Upstash)
- [ ] `OPENROUTER_API_KEY`

### ✅ Infrastructure Supabase
- [ ] Trigger SQL `on_message_notify_bot` créé
- [ ] Au moins 1 bot profile existe
- [ ] Tables nécessaires créées

---

## 🎯 Option Recommandée : Tests Locaux D'abord

**Temps estimé :** 30 minutes  
**Pourquoi :** Valide que tout fonctionne avant production

### Test Local Rapide

```bash
# 1. Activer environnement
cd /Users/anthony/Projects/randomatch-bot-service
source venv/bin/activate

# 2. Vérifier config
python -m app.test_config

# 3. Terminal 1 : Bridge
python -m app.bridge_intelligence

# 4. Terminal 2 : Worker
python -m app.worker_intelligence

# 5. Observer les logs
# Si pas d'erreurs pendant 1-2 minutes → prêt à deploy
```

**Signes que ça fonctionne :**
- Bridge : "✅ Connecté au canal bot_events"
- Worker : "🤖 Worker Intelligence démarré"
- Pas d'exceptions Python
- Pas d'erreurs connexion

---

## 🚀 Déploiement Railway

### Étape 1 : Préparation Git

```bash
# Vérifier fichiers non commités
git status

# Ajouter tous les nouveaux fichiers
git add .

# Commit avec message clair
git commit -m "feat: Phase 1-2 complete - Bot Intelligence with grouping and adaptive timing"

# Push vers GitHub
git push origin main
```

### Étape 2 : Configuration Railway

1. **Connecter le Repo**
   - Va sur [railway.app/dashboard](https://railway.app/dashboard)
   - "New Project" → "Deploy from GitHub repo"
   - Sélectionner `randomatch-bot-service`

2. **Ajouter Variables d'Environnement**
   - Settings → Variables
   - Ajouter TOUTES les variables :

```env
SUPABASE_URL=https://xxxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOi...
POSTGRES_CONNECTION_STRING=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
REDIS_URL=redis://default:password@xxxxx.upstash.io:6379
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=x-ai/grok-4-fast
LOG_LEVEL=INFO
ENVIRONMENT=production
```

3. **Vérifier Procfile**
   - Railway détecte automatiquement le Procfile
   - Vérifie que 2 processus sont configurés :
     - `bridge` : Bridge Intelligence
     - `worker` : Worker Intelligence

### Étape 3 : Premier Déploiement

Railway va automatiquement :
1. Installer les dépendances (`requirements.txt`)
2. Lancer les 2 processus (bridge + worker)
3. Exposer les logs

**Temps de build :** 2-3 minutes

### Étape 4 : Vérification Déploiement

```bash
# Installer Railway CLI (si pas fait)
npm i -g @railway/cli

# Login
railway login

# Lier le projet
railway link

# Voir logs temps réel
railway logs --tail
```

**Logs attendus :**

```
[bridge] 🌉 Bridge Intelligence - Démarrage
[bridge] 📡 Connexion PostgreSQL...
[bridge] ✅ Connecté au canal bot_events
[bridge] 👂 Écoute des notifications...

[worker] 🤖 Worker Intelligence - Démarrage
[worker] 📦 Connexion Redis...
[worker] ✅ Redis connecté
[worker] 👂 En attente de messages...
```

### Étape 5 : Test Production

1. **Via Flutter App**
   - Ouvre RandoMatch
   - Match avec un bot (Camille ou Paul)
   - Envoie un message : "Salut !"
   - Observe :
     - Typing indicator apparaît après 3-5s
     - Bot "tape" pendant quelques secondes
     - Réponse arrive naturellement

2. **Via Logs Railway**
   ```bash
   railway logs --tail
   ```
   
   Tu devrais voir :
   ```
   [bridge] 📨 Notification reçue: message_id=xxx
   [bridge] ✅ Message poussé dans queue
   [worker] 🤖 TRAITEMENT MESSAGE INTELLIGENT
   [worker] 📦 Phase 1: Pre-processing...
   [worker] 🧠 Phase 2: Analyse contextuelle...
   [worker] ⏱️ Phase 3: Calcul timing...
   [worker] ⌨️ Phase 4: Activation typing...
   [worker] 🧠 Phase 5: Génération réponse IA...
   [worker] 📤 Phase 6: Envoi message...
   [worker] ✅ Message traité avec succès !
   ```

---

## 🐛 Troubleshooting Déploiement

### Problème : Build échoue

**Symptôme :** Railway affiche erreur pendant build

**Solutions :**
1. Vérifier `requirements.txt` est correct
2. Vérifier Python 3.11+ spécifié
3. Regarder logs build détaillés

### Problème : Bridge ne démarre pas

**Symptôme :** Erreur "Can't connect to PostgreSQL"

**Solutions :**
1. Vérifier `POSTGRES_CONNECTION_STRING` correct
2. Vérifier IP whitelisting Supabase (Railway IPs)
3. Tester connexion avec `psql`

### Problème : Worker ne reçoit rien

**Symptôme :** Logs worker silencieux

**Solutions :**
1. Vérifier `REDIS_URL` correct
2. Tester Redis : `redis-cli -u $REDIS_URL ping`
3. Vérifier que bridge pousse dans Redis

### Problème : Bot ne répond pas

**Symptôme :** Message envoyé mais pas de réponse

**Solutions :**
1. Vérifier logs Railway pour erreurs
2. Vérifier trigger SQL actif dans Supabase
3. Vérifier bot_id existe dans bot_profiles
4. Vérifier OpenRouter API key valide

---

## 📊 Monitoring Post-Déploiement

### Métriques à Surveiller

**Railway Dashboard :**
- CPU usage (devrait être < 50%)
- Memory usage (devrait être < 200MB)
- Restart count (devrait être 0)

**Logs à Surveiller :**
- Erreurs PostgreSQL
- Erreurs Redis
- Erreurs OpenRouter API
- Exceptions Python

### Commandes Utiles

```bash
# Logs temps réel
railway logs --tail

# Filtrer par service
railway logs --service bridge
railway logs --service worker

# Restart un service
railway restart

# Voir variables env
railway variables
```

---

## 🔄 Rollback si Problème

Si problème majeur en production :

### Plan A : Désactiver Nouveau Système

```sql
-- Dans Supabase SQL Editor
DROP TRIGGER IF EXISTS on_message_notify_bot ON messages;

-- Si ancien système existe, le réactiver
-- (voir sql/cleanup_old_system.sql)
```

### Plan B : Rollback Git

```bash
# Revenir au commit précédent
git log --oneline  # Voir historique
git revert HEAD    # Annuler dernier commit
git push origin main  # Railway redeploy automatiquement
```

### Plan C : Pause Railway

- Dashboard Railway → Settings → "Pause Deployment"
- Donne temps de fix sans utiliser ressources

---

## ✅ Checklist Post-Déploiement

### Immédiat (0-5 min)
- [ ] 2 processus (bridge + worker) running
- [ ] Pas d'erreurs dans logs
- [ ] CPU/Memory normaux

### Court Terme (5-30 min)
- [ ] Test message simple fonctionne
- [ ] Typing indicator visible
- [ ] Réponse naturelle reçue
- [ ] Test messages rapides (grouping)

### Moyen Terme (30 min - 2h)
- [ ] Plusieurs conversations testées
- [ ] Pas de crash
- [ ] Timing adaptatif observé
- [ ] Multi-messages testés

### Long Terme (2h+)
- [ ] Stabilité 24h
- [ ] Pas de memory leak
- [ ] Performance constante
- [ ] Utilisateurs satisfaits

---

## 🎯 Next Steps Après Deploy Réussi

### Court Terme
1. **Monitoring :** Setup alertes Railway
2. **Docs :** Mettre à jour README avec URL prod
3. **Tests :** Tests de charge (10+ conversations)

### Moyen Terme
1. **Phase 3 :** Prompt Builder avancé
2. **Phase 4 :** Memory Manager
3. **Phase 5 :** Celery + features production

### Long Terme
1. **Optimization :** Tuning délais selon feedback users
2. **Scaling :** Plus de workers si besoin
3. **Features :** Mémoire conversationnelle avancée

---

## 📞 Support

**Questions ? Problèmes ?**

- GitHub Issues : [repo issues]
- Railway Docs : https://docs.railway.app
- Supabase Docs : https://supabase.com/docs

---

**Dernière mise à jour :** 18 octobre 2025  
**Version :** 2.1.0 - Intelligence Conversationnelle  
**Status :** Prêt pour déploiement ✅
