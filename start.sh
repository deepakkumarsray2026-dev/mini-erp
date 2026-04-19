#!/usr/bin/env bash
# start.sh — Start the mini-ERP dev stack
set -euo pipefail

COMPOSE="docker compose -f docker-compose.dev.yml"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_DIR"

# ---------- helpers ----------
log()  { echo "[$(date '+%H:%M:%S')] $*"; }
ok()   { echo "[$(date '+%H:%M:%S')] OK  $*"; }
fail() { echo "[$(date '+%H:%M:%S')] ERR $*" >&2; exit 1; }

# ---------- pre-flight ----------
command -v docker >/dev/null 2>&1 || fail "docker is not installed"
docker compose version >/dev/null 2>&1 || fail "docker compose plugin not found"

[[ -f backend/.env.dev ]] || fail "backend/.env.dev not found — copy .env.dev.example and fill in values"

# ensure host dirs exist (volumes)
mkdir -p models uploads logs

# ---------- build & start ----------
log "Building images (skipped if up-to-date)..."
$COMPOSE build --quiet

log "Starting all services..."
$COMPOSE up -d

# ---------- wait for backend health ----------
log "Waiting for backend to become healthy..."
MAX=30; COUNT=0
until $COMPOSE exec -T backend curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; do
  COUNT=$((COUNT + 1))
  [[ $COUNT -ge $MAX ]] && fail "Backend did not become healthy after ${MAX} attempts. Run: $COMPOSE logs backend"
  sleep 3
done
ok "Backend is healthy"

# ---------- migrations ----------
log "Running Alembic migrations..."
$COMPOSE exec -T -e PYTHONPATH=/app backend alembic upgrade head
ok "Migrations applied"

# ---------- status ----------
echo ""
echo "================================================"
echo " mini-ERP dev stack is up"
echo "================================================"
echo " API:      http://localhost:8000"
echo " API docs: http://localhost:8000/docs"
echo " Frontend: http://localhost:3000"
echo " DB:       localhost:5432  (mini_erp / erp_user)"
echo " Redis:    localhost:6379"
echo ""
$COMPOSE ps
echo ""
echo "Tip: docker compose -f docker-compose.dev.yml logs -f backend"
