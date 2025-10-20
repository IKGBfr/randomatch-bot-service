# ⚡ FIX 2 MIN - Bot Ne Répond Pas

## 🎯 PROBLÈME
Worker ne traite JAMAIS les messages → Bot ne répond pas

## ✅ SOLUTION
Railway doit lancer bridge + worker EN PARALLÈLE

---

## 🚀 DÉPLOIE MAINTENANT

```bash
cd /Users/anthony/Projects/randomatch-bot-service
chmod +x deploy_fix_no_response.sh
./deploy_fix_no_response.sh
```

**PUIS dans Railway Dashboard :**

Settings → Deploy → **Start Command** :
```
python -m app.unified_service
```

---

## 🧪 TEST

Flutter → Envoie "Salut !" → Bot répond en 5-15s ✅

---

**Durée Fix :** 2 minutes  
**Impact :** Bot fonctionnel
