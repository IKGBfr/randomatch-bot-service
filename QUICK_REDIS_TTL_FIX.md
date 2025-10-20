# ⚡ Quick Fix - Redis TTL

## Problème
Bot ne répond plus → **TTL contexte (10s) < Timer grouping (15s)**

## Solution
```python
# app/redis_context.py
self.CONTEXT_TTL = 20  # ✅ Était 10
```

## Déploiement
```bash
chmod +x deploy_redis_ttl_fix.sh
./deploy_redis_ttl_fix.sh
```

**Attendre 60s rebuild.**

## Validation
Envoyer message → Bot répond après ~20s ✅

---

**Règle :** `TTL >= TIMER + MARGE`
