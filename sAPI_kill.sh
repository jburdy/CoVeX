#!/usr/bin/env sh

pids=$(lsof -ti:8000)

if [ -z "$pids" ]; then
    echo "Aucun backend actif sur le port 8000."
    exit 0
fi

kill $pids
echo "Backend arrete: $pids"
