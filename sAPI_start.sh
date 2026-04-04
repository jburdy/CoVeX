#!/usr/bin/env sh
pids=$(lsof -ti:8000)

if [ -z "$pids" ]; then
    kill $pids
    echo "Backend arrete: $pids"
    uv run --project backend uvicorn main:app --app-dir backend/src --reload
    exit 0
fi



