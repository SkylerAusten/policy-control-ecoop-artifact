#!/usr/bin/env bash

set -euo pipefail

BUNDLE_DIR="${1:-pick-policy-control-study}"
BUNDLE_DIR="${BUNDLE_DIR%/}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

APP_IMAGE_TAG="pick-policy-control-study-app:artifact"
DB_IMAGE_TAG="mysql:8.4"
OUTPUT_TAR="$BUNDLE_DIR/images.tar"
COMPOSE_OUT="$BUNDLE_DIR/compose.yaml"
README_OUT="$BUNDLE_DIR/README.txt"
ARCHIVE_OUT="$BUNDLE_DIR.tar.gz"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker command not found in Git Bash. Start Docker Desktop and ensure docker is available in PATH." >&2
  exit 1
fi

cd "$PROJECT_ROOT"
mkdir -p "$BUNDLE_DIR"

echo "[1/3] Building app image: $APP_IMAGE_TAG"
docker build -t "$APP_IMAGE_TAG" .

echo "[2/3] Pulling DB image: $DB_IMAGE_TAG"
docker pull "$DB_IMAGE_TAG"

echo "[3/3] Saving images to $OUTPUT_TAR"
docker save -o "$OUTPUT_TAR" "$APP_IMAGE_TAG" "$DB_IMAGE_TAG"

cp "docker-compose.artifact.yml" "$COMPOSE_OUT"

cat >"$README_OUT" <<EOF
Artifact quickstart:

1) Load images:
   docker image load -i $(basename "$OUTPUT_TAR")

2) Start services:
   docker compose up -d

3) Open app:
   http://localhost:8080

4) Stop services:
   docker compose down
EOF

echo "[4/4] Creating compressed archive: $ARCHIVE_OUT"
tar -czf "$ARCHIVE_OUT" "$BUNDLE_DIR"

echo "Done. Created reviewer bundle at $BUNDLE_DIR"
echo "Created archive at $ARCHIVE_OUT"
echo "Share '$ARCHIVE_OUT' (or the entire '$BUNDLE_DIR' folder)."