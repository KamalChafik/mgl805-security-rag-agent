#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v docker >/dev/null 2>&1; then echo 'ERROR: Docker not found.' >&2; exit 1; fi
if ! docker compose version >/dev/null 2>&1; then echo 'ERROR: Docker Compose plugin not found.' >&2; exit 1; fi
if ! docker info >/dev/null 2>&1; then echo 'ERROR: Cannot access Docker daemon. Check user permissions.' >&2; exit 1; fi
if [[ ! -f .env ]]; then cp .env.example .env; chmod 600 .env; echo 'Created .env from .env.example'; fi
chmod 600 .env
# Only generate unknown secrets once. Existing values are preserved on later runs.
set_env_if_blank() {
  local key="$1" value
  if ! grep -q "^${key}=" .env; then echo "${key}=" >> .env; fi
  if ! grep -Eq "^${key}=.+" .env; then
    if command -v openssl >/dev/null 2>&1; then value=$(openssl rand -hex 32)
    elif command -v python3 >/dev/null 2>&1; then value=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    else echo 'ERROR: openssl or Python3 needed to generate secrets.' >&2; exit 1; fi
    local temp; temp=$(mktemp)
    sed "s|^${key}=$|${key}=${value}|" .env > "$temp"
    cat "$temp" > .env
    rm -f "$temp"
    echo "Generated ${key} in .env"
  fi
}
set_env_if_blank WEBUI_SECRET_KEY
set_env_if_blank DB_PASSWORD
set_env_if_blank DB_ROOT_PASSWORD
for d in data/reports data/zap data/openwebui data/chroma data/mariadb data/state backups; do mkdir -p "$d"; done
# Do not chmod -R 777 or chown across user's existing persistent data.
echo 'Checking Compose configuration ...'
docker compose --env-file .env config --quiet

if [[ "${1:-}" == '--check-only' ]]; then echo 'Compose configuration is valid.'; exit 0; fi

# An existing Portainer deployment can reserve the same host ports. Never auto-remove it.
echo 'Starting containers (external Windows Ollama is NOT started by this script) ...'
docker compose --env-file .env up -d --build

echo
echo 'Containers:'
docker compose ps
echo
echo 'Next: read README.md, create Open WebUI admin and knowledge base, then fetch/upload OWASP documents.'
echo 'If ZAP cannot write reports, use the documented ownership fix. Never commit data/ or .env.'
