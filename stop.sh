#!/usr/bin/env bash
# stop.sh — Stop the mini-ERP dev stack
set -euo pipefail

COMPOSE="docker compose -f docker-compose.dev.yml"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_DIR"

# ---------- helpers ----------
log()  { echo "[$(date '+%H:%M:%S')] $*"; }
ok()   { echo "[$(date '+%H:%M:%S')] OK  $*"; }

# ---------- stop ----------
log "Stopping all services..."
$COMPOSE down

ok "All services stopped"
echo ""
echo "================================================"
echo " mini-ERP dev stack is down"
echo "================================================"
echo ""
echo "Tip: run ./start.sh to bring it back up"
