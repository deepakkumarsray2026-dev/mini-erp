#!/usr/bin/env bash
# Pull the Ollama models needed for Phase 3 LLM/RAG.
# Run this ONCE after starting the stack for the first time.
#
# Usage:
#   bash scripts/pull_ollama_models.sh

set -e

echo "Pulling llama3.2:3b (~2.0 GB) — chat model..."
docker compose -f docker-compose.dev.yml exec ollama ollama pull llama3.2:3b

echo "Pulling nomic-embed-text (~274 MB) — embedding model..."
docker compose -f docker-compose.dev.yml exec ollama ollama pull nomic-embed-text

echo ""
echo "Done. Models are stored in the ollama_data volume and persist across restarts."
echo "You can verify with: docker compose -f docker-compose.dev.yml exec ollama ollama list"
