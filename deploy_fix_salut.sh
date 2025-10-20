#!/bin/bash

echo "🔧 DÉPLOIEMENT FIX 'SALUT ALBERT' EN PLEINE CONVERSATION"
echo "========================================================="
echo ""
echo "PROBLÈME RÉSOLU:"
echo "- Bot commençait par 'Salut Albert' même en pleine conversation"
echo "- Ex: Message 20+ dans une conversation : 'Salut Albert, tu demandes...'"
echo ""
echo "CAUSE:"
echo "- Prompt ne disait pas explicitement de NE PAS commencer par 'Salut'"
echo "- Grok générait naturellement cette formule d'ouverture"
echo ""
echo "FIX:"
echo "- Instructions EXPLICITES selon phase conversation"
echo "- Message 0 : OK 'Salut [Prénom]'"
echo "- Messages 1-5 : Ne PAS recommencer par 'Salut'"
echo "- Messages 5+ : NE JAMAIS JAMAIS commencer par 'Salut'"
echo ""
echo "FICHIERS MODIFIÉS:"
echo "- app/prompt_builder.py : Adaptation style selon historique"
echo ""
read -p "Déployer sur Railway ? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📦 Commit des changements..."
    git add app/prompt_builder.py
    git commit -m "fix(prompt): Empêche 'Salut [Prénom]' en pleine conversation

- Problème: Bot commençait par 'Salut Albert' au message 20+
- Cause: Aucune instruction explicite contre ça dans le prompt
- Fix: Adaptation style selon nombre de messages
  * 0 messages: OK 'Salut [Prénom]'
  * 1-5: Ne PAS recommencer par 'Salut'
  * 5+: NE JAMAIS commencer par 'Salut [Prénom]'
- Impact: Conversation plus naturelle et cohérente"
    
    echo ""
    echo "🚀 Push vers Railway..."
    git push origin main
    
    echo ""
    echo "✅ DÉPLOYÉ !"
    echo ""
    echo "⏱️  Attendre 60s pour rebuild Railway..."
    echo ""
    echo "🧪 TESTS À FAIRE:"
    echo "1. Continuer conversation existante (10+ messages)"
    echo "2. Vérifier que bot NE COMMENCE PAS par 'Salut Albert'"
    echo "3. Vérifier que bot commence directement par réponse"
    echo ""
    echo "✅ ATTENDU:"
    echo "- 'Ah cool !' ✓"
    echo "- 'Vraiment ?' ✓"
    echo "- 'J'adore' ✓"
    echo ""
    echo "❌ PAS ATTENDU:"
    echo "- 'Salut Albert' ✗"
    echo "- 'Hello' ✗"
    echo "- 'Hey' ✗"
    echo ""
else
    echo ""
    echo "❌ Déploiement annulé"
fi
