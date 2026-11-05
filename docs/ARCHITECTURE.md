# Architecture — MGL805 Security Lab

## What runs where

The Linux VM hosts Open WebUI, ChromaDB, FastAPI, ZAP Webswing, DVWA and MariaDB in one Docker Compose project. Ollama (Qwen3.5:9b and Qwen3 Embedding 0.6b) continues to run on the Windows PC with RTX 3060 12 GB. This is by design: a single **Compose project** does not imply that every component is colocated physically.

## Two distinct paths

**Knowledge ingestion (managed by Open WebUI):** Official OWASP files → `scripts/load_knowledge.py` using Open WebUI API → Open WebUI file processing/chunking → Ollama embeddings → Open WebUI writes vectors + chunks + metadata to ChromaDB. The loader does not bypass Open WebUI.

**Agent runtime (explicit tool calls):** User → Open WebUI/Qwen → `OWASP Report Bridge`. The bridge reads FastAPI ZAP findings using HTTP, and retrieves OWASP chunks by calling Ollama embeddings then querying the existing Chroma collection. The model correlates the two. For this setup, don't attach a huge automatic Knowledge context at the same time you are testing tool calls.

## Docker isolation

- `backend`: Open WebUI, ChromaDB, FastAPI. Open WebUI and the bridge can call the external Windows Ollama URL. No host-published Chroma/FastAPI port.
- `lab` (internal): ZAP, DVWA, FastAPI, intentionally isolated from external destinations. ZAP/agent reach DVWA as `http://dvwa:80/`.
- `dbnet` (internal): DVWA and MariaDB only. MariaDB must not be visible to ZAP or other app containers.

ZAP's Webswing GUI is published on host port 8088; its control/proxy port 8090 remains internal. ZAP root CA keys live under `data/zap/`. FastAPI only sees `data/reports/` read-only.

## Limitations

- The lab target is DVWA, not your colleague's remote Juice Shop environment.
- No scan-launch API function exists. Adding one will require a scoped, authenticated security boundary and explicit user approval for intrusive scans.
- The exact Chroma collection UUID is generated at knowledge-base creation. The source material may produce more or fewer than 161 chunks depending on settings.
- The host-side `.env` values may not override UI settings already persisted by Open WebUI. Verify the actual admin configuration.
