#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
docker compose stop
printf 'Stopped Compose services. Persistent data is preserved.\n'
