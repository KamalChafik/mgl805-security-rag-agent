#!/usr/bin/env bash
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.."
echo '=== Compose ==='
docker compose ps || exit 1
printf '\n=== Open WebUI backend health ===\n'
docker compose exec -T open-webui python -c 'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=10).read().decode()[:500])' || true
printf '\n=== Chroma heartbeat ===\n'
docker compose exec -T open-webui python -c 'import chromadb; print(chromadb.HttpClient(host="chromadb",port=8000).heartbeat())' || true
printf '\n=== FastAPI report inventory ===\n'
docker compose exec -T open-webui python -c 'import urllib.request; print(urllib.request.urlopen("http://security-agent:8000/reports",timeout=10).read().decode()[:1500])' || true
printf '\n=== Ollama model inventory (inside Open WebUI) ===\n'
docker compose exec -T open-webui python -c 'import os,urllib.request; print(urllib.request.urlopen(os.environ["OLLAMA_BASE_URL"].rstrip("/")+"/api/tags",timeout=8).read().decode()[:1500])' || true
printf '\n=== DVWA from security-agent ===\n'
docker compose exec -T security-agent python -c 'import urllib.request; print(urllib.request.urlopen("http://dvwa:80/",timeout=8).status)' || true
printf '\nNOTE: ZAP API/control port 8090 is not assumed functional. Start Webswing GUI in browser first.\n'
