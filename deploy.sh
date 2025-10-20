#!/bin/bash

# Commit and deploy bot service changes
echo "📦 Committing changes..."
cd /Users/anthony/Projects/randomatch-bot-service

git add app/worker_intelligence.py
git add app/pre_processing.py  
git add app/bridge_intelligence.py

git commit -m "fix: bot abandons completely when user is typing

- Worker: ABANDON total si typing détecté, repousse avec retry counter
- Pre-processing: Check typing fraîcheur (<5s) pour détection précise
- Bridge: Grouping delay 5s + reset timer à chaque nouveau message
- Max 5 retry pour éviter boucles infinies"

echo "🚀 Pushing to GitHub..."
git push origin main

echo "✅ Done! Railway will auto-deploy in 30-60s"
echo "📝 Changes:"
echo "  - Bot abandonne complètement si tu tapes encore"
echo "  - Attend que tu aies vraiment fini avant de répondre"  
echo "  - Grouping amélioré (5s avec reset du timer)"
