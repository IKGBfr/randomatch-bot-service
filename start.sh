#!/bin/bash

# Lance bridge + worker en parallèle
echo "🚀 Démarrage Bridge + Worker en parallèle..."

# Bridge en arrière-plan
python -m app.bridge_intelligence &
BRIDGE_PID=$!
echo "✅ Bridge PID: $BRIDGE_PID"

# Worker en avant-plan (pour voir logs)
python -m app.main_worker &
WORKER_PID=$!
echo "✅ Worker PID: $WORKER_PID"

# Attendre les deux processus
wait $BRIDGE_PID $WORKER_PID
