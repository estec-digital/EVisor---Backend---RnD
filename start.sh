#!/bin/bash
set -a
source .env
set +a

echo "🔄 Starting Docker Compose..."
docker compose up -d
