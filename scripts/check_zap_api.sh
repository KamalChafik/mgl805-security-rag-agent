#!/usr/bin/env bash
# Read-only API version check, key is read interactively and never echoed.
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [[ ! -t 0 ]]; then echo 'Interactive terminal required (do not pass ZAP API key on CLI).' >&2; exit 1; fi
read -rsp 'ZAP API key (press Enter to test without one): ' APIKEY
echo
printf '%s' "$APIKEY" | docker compose exec -T zap python3 -c '
import sys, urllib.request, urllib.error
key=sys.stdin.read().strip()
headers={"X-ZAP-API-Key":key} if key else {}
req=urllib.request.Request("http://127.0.0.1:8090/JSON/core/view/version/",headers=headers)
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
    res=opener.open(req,timeout=12)
    print(res.status, res.read(400).decode(errors="replace"))
except urllib.error.HTTPError as e:
    print("HTTP",e.code,e.read(400).decode(errors="replace"))
except Exception as e:
    print("ZAP API unavailable:", type(e).__name__, str(e))
'
unset APIKEY
