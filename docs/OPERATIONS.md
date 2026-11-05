# Operations / Troubleshooting

## Diagnosing 'Model qwen3.5:9b not found'

This error may indicate Ollama is **unreachable**, not that the model is absent. On Windows run `ollama list` and `ollama ps`, then `curl.exe http://127.0.0.1:11434/api/tags`. On the Linux VM run `curl --max-time 8 http://WINDOWS_IP:11434/api/tags`. Inside Open WebUI, `./scripts/check_stack.sh` tests the configured endpoint. Verify actual Windows IPv4 address, `OLLAMA_HOST` binding, Windows Firewall scope, routes, and `.env` `OLLAMA_URL`. The bridge inherits the same URL through container environment.

## Open WebUI custom tool says no tools found

Use the Python **Workspace Tool** in `openwebui/tools/owasp_report_bridge.py`; this was verified to work in our lab even when an external OpenAPI server tool showed `No tools found`. In the model profile disable Builtin Tools, set Function Calling = Native, enable the bridge and start a fresh chat. Confirm the four functions appear. Do not assume a model's text saying it has no tools is proof of a network failure; inspect the tool invocation list and backend behavior.

## Direct knowledge attachment causes tool skipping

Our Qwen3.5 9B sometimes answered from retrieved knowledge (e.g., 11 sources) instead of invoking FastAPI tools. Test custom tools with no auto-attached knowledge base, then explicitly call `search_owasp_knowledge`. If a different model works with automatic RAG and tools, you may enable that mode after validation.

## ZAP shows Webswing but API is closed

Port 8080 inside the container is Webswing, published as port 8088. It is not the API. Port 8090 is ZAP's API/proxy, but must first be initialized by opening `/zap` in the browser. The previous environment returned `RemoteDisconnected` from port 8090, even inside the ZAP container; this was **not solved**. Check Tools → Options → API (API key and allowed addresses), Network → Local Servers/Proxies (address and API/proxy mode), and ZAP logs. `./scripts/check_zap_api.sh` provides a version-only authenticated probe. Do not publish port 8090 or disable API authentication as a workaround.

## Report import and permissions

Saved reports should have a top-level ZAP `site` array. Use:

```bash
python3 scripts/import_zap_report.py /path/to/report.json
python3 scripts/summarize_zap_report.py
```

If the ZAP Report dialogue saves `report.html`, also export a separate `report.json`; the FastAPI parser does not parse HTML or PDF. The ZAP container saves to `/zap/wrk/reports`, host folder `data/reports`. FastAPI's `/reports` is read-only. If files seem invisible, check host folder ownership and `docker compose exec security-agent ls -l /reports` (if `ls` is available; its Python image is slim).

## Knowledge import issues

- API token must be from the intended Open WebUI account; don't paste it publicly.
- A **Knowledge ID** is distinct from a file ID or model ID.
- File processing is asynchronous: the loader polls for `completed` before calling `file/add`.
- If you get a duplicate content error, it can mean the content was already indexed. Do not blindly `--force` in a loop.
- If `check_chroma.py` reports no configured collection, edit `.env` `KNOWLEDGE_ID` and recreate **open-webui** only (`docker compose up -d --no-deps --force-recreate open-webui`).
- If changing the embedding model, re-embed/reindex documents in a new collection; matching dimensions by themselves do not prove embedding space compatibility.
- Large imports can take several minutes because Ollama runs on a different machine.

## Backups and upgrades

Use `./scripts/backup.sh --yes` for an offline filesystem snapshot (stack stopped during tar). It includes `.env`, account data, Chroma and MariaDB files, reports and ZAP CA keys. Secure or encrypt that archive. `docker compose pull && docker compose up -d --build` is appropriate only after reading release notes and taking a backup. Preserve `.env` stable keys to retain Open WebUI sessions and DB credentials. Do **not** run `docker compose down -v` unless intentionally destroying data.

## Other useful inspections

```bash
docker compose config --quiet
docker compose ps
docker compose logs --tail=100 chromadb
docker compose logs --tail=100 zap
docker compose exec -T open-webui python -c 'import urllib.request; print(urllib.request.urlopen("http://security-agent:8000/reports").read().decode())'
python3 scripts/check_chroma.py --query 'SQL injection CWE-89'
./scripts/run-tests.sh
```
