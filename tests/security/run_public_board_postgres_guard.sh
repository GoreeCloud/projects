#!/usr/bin/env bash
# Copyright (c) 2026 GoreeCloud
# SPDX-License-Identifier: AGPL-3.0-only
#
# Disposable PostgreSQL 17 predicate check for synthetic public boards.
# No network, published port, host bind mount, credentials or persistence.
# NOT a Plane/Django full-stack test and NEVER intended for production data.
set -euo pipefail

if ! command -v podman >/dev/null 2>&1; then
  echo "Podman is required for the optional offline PostgreSQL check." >&2
  exit 2
fi

IMAGE="docker.io/library/postgres:17"
if ! podman image exists "$IMAGE"; then
  echo "PostgreSQL 17 image must be inspected and available locally; never auto-pull." >&2
  exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
SQL_FILE="$SCRIPT_DIR/public_board_postgres_guard.sql"
test -r "$SQL_FILE"

NAME="gc-projects-postgres-smoke-$(id -u)-$$"
CID=""
cleanup() {
  # Stop only the exact disposable container created in this invocation.
  if [[ -n "$CID" ]]; then
    podman stop --time 2 "$CID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

# The image is preinstalled and its entrypoint must be reviewed before use.
# POSTGRES_HOST_AUTH_METHOD=trust is safe ONLY with --network=none and no
# published port; access is confined to psql via podman exec in this container.
CID="$(podman run \
  --pull=never --rm --detach --name "$NAME" \
  --network=none --read-only --user postgres \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --memory=512m --pids-limit=128 \
  --tmpfs /tmp:rw,mode=1777,size=256m \
  --tmpfs /var/run/postgresql:rw,mode=1777,size=32m \
  -e PGDATA=/tmp/gc-postgres-tempdata \
  -e POSTGRES_HOST_AUTH_METHOD=trust \
  "$IMAGE")"

ready=0
for _ in {1..24}; do
  if podman exec "$CID" pg_isready -U postgres >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != "1" ]]; then
  echo "Isolated PostgreSQL did not become ready." >&2
  exit 1
fi

echo "Running synthetic PostgreSQL predicates in a network-disabled container."
podman exec -i "$CID" psql -X -v ON_ERROR_STOP=1 -U postgres -d postgres < "$SQL_FILE"
echo "Isolated PostgreSQL public-board predicate and revocation checks passed."
