# ⚡ QUICK FIX - Initiation Double

## 🐛 Problème
Bot envoyait "Salut Albert" en plein conversation.

## 🔍 Cause
`match_monitor.py` vérifiait SEULEMENT messages de l'user :
```python
"sender_id": f"eq.{initiation['user_id']}"  # ❌ SEULEMENT USER
```

Si bot avait initié, ne détectait pas conversation existante.

## ✅ Solution
Vérifie TOUS les messages (bot OU user) :
```python
# On ne filtre PAS par sender_id → vérifie TOUS les messages
"match_id": f"eq.{initiation['match_id']}"  # ✅ TOUS
```

## 🚀 Déployer
```bash
./deploy_initiation_fix.sh
```

## 🧪 Test
Logs doivent montrer :
```
🚫 Initiation xxx annulée (conversation existe déjà)
```

## 📁 Fichier
`app/match_monitor.py` - Méthode `_send_initiation()`
