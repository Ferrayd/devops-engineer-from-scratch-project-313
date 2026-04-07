#!/bin/bash

set -e

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

cleanup() {
    log "Shutting down..."
    kill $NGINX_PID $UVICORN_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT

log "Starting Nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!
sleep 1

log "Starting Uvicorn..."
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
UVICORN_PID=$!

log "Services started. Nginx PID: $NGINX_PID, Uvicorn PID: $UVICORN_PID"

wait $NGINX_PID $UVICORN_PID