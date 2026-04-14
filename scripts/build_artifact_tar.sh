#!/usr/bin/env bash

set -euo pipefail

BUNDLE_DIR="${1:-pick-policy-control-study}"
BUNDLE_DIR="${BUNDLE_DIR%/}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

APP_IMAGE_TAG="pick-policy-control-study-app:artifact"
DB_IMAGE_TAG="mysql:8.4"
OUTPUT_TAR="$BUNDLE_DIR/images.tar"
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

cat >"$README_OUT" <<EOF
Artifact quickstart:

1) Load images:
   docker image load -i $(basename "$OUTPUT_TAR")

2a) Run with SQLite (no MySQL required):
    docker run -d --name pick-app -p 8080:8080 $APP_IMAGE_TAG

2b) Or run with MySQL:
    docker network create pick-net
    docker run -d --name pick-db --network pick-net \\
      -e MYSQL_DATABASE=pick_policy-control_app \\
      -e MYSQL_USER=appuser \\
      -e MYSQL_PASSWORD=apppassword \\
      -e MYSQL_ROOT_PASSWORD=rootpassword \\
      $DB_IMAGE_TAG
    docker run -d --name pick-app --network pick-net -p 8080:8080 \\
      -e DB_USER=appuser -e DB_PASSWORD=apppassword \\
      -e DB_HOST=pick-db -e DB_PORT=3306 \\
      -e DB_NAME=pick_policy-control_app \\
      $APP_IMAGE_TAG

3) Open app:
   http://localhost:8080

4) Stop and clean up:
   docker rm -f pick-app pick-db 2>/dev/null
   docker network rm pick-net 2>/dev/null
EOF

echo "[4/4] Creating compressed archive: $ARCHIVE_OUT"
tar -czf "$ARCHIVE_OUT" "$BUNDLE_DIR"

echo "Done. Created reviewer bundle at $BUNDLE_DIR"
echo "Created archive at $ARCHIVE_OUT"
echo "Share '$ARCHIVE_OUT' (or the entire '$BUNDLE_DIR' folder)."