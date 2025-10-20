#!/bin/bash
cd /Users/anthony/Projects/randomatch-bot-service
git add app/worker_intelligence.py app/pre_processing.py app/bridge_intelligence.py
git commit -m "fix: bot abandons completely when user is typing

- Worker: ABANDON total si typing détecté, repousse avec retry counter
- Pre-processing: Check typing fraîcheur (<5s) pour détection précise
- Bridge: Grouping delay 5s + reset timer à chaque nouveau message
- Max 5 retry pour éviter boucles infinies"
git push origin main