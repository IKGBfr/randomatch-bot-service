# ⚡ QUICK FIX - "Salut Albert" en Pleine Conversation

## 🐛 Problème
Bot commençait par "Salut [Prénom]" au message 20+ d'une conversation.

## 🔍 Cause
Prompt ne disait PAS explicitement de ne pas faire ça après le 1er message.

## ✅ Solution
Instructions adaptatives selon nombre de messages :

```python
if message_count == 0:
    # ✅ "Salut [Prénom]" OK
elif message_count < 5:
    # ⚠️ Ne PAS recommencer par "Salut"
else:
    # ❌ NE JAMAIS "Salut [Prénom]"
    # Exemples BON: "Ah cool !", "Vraiment ?"
    # Exemples MAUVAIS: "Salut Albert", "Hey"
```

## 🚀 Déployer
```bash
./deploy_fix_salut.sh
```

## 🧪 Test
Message 15+ doit commencer directement :
- ✅ "Ah cool !"
- ❌ "Salut Albert"

## 📁 Fichier
`app/prompt_builder.py` - Méthode `build_full_prompt()`
