#!/usr/bin/env bash
# Consistent, offline snapshot: briefly stops ALL services; archive includes secrets.
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [[ "${1:-}" != '--yes' ]]; then
  echo 'This stops the stack briefly and creates a SENSITIVE archive of .env and data/.'
  echo 'Usage: ./scripts/backup.sh --yes'; exit 2
fi
mkdir -p backups
umask 077
archive="backups/mgl805-$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
restarted=0
restart() { if [[ "$restarted" -eq 0 ]]; then docker compose start >/dev/null || true; restarted=1; fi; }
trap restart EXIT
printf 'Stopping stack for consistent snapshot ...\n'
docker compose stop
# EXCLUDE symlinks and unknown external data sources; backup includes persistent bind mounts and .env.
tar -czf "$archive" .env compose.yaml data/
printf 'Saved %s\n' "$archive"
restart
printf 'Restarted. Keep the backup encrypted/offsite; it contains keys, records and ZAP certificates.\n'
