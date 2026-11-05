# Roadmap / feature boundaries

## Already implemented here

- One Docker Compose project: Open WebUI, ChromaDB, Security Agent, ZAP Webswing, DVWA, MariaDB.
- Windows Ollama connectivity configured via `.env` (external dependency, not launched by Compose).
- Manual Open WebUI Python Workspace Tool with four functions.
- Official OWASP Top 10:2025 fetch script; authenticated Open WebUI API ingestion; local SHA256 state; Chroma inspection and semantic retrieval checks.
- Read-only FastAPI report API and utility scripts for report import, summaries, tests, health, backups.

## Future milestones (NOT in this version)

1. Resolve ZAP Webswing port 8090 API access; securely authenticate using a vault/secret and restrict clients. Add a read-only API status tool first.
2. Design scan job orchestration with explicit target allowlist, user approval, limits, progress tracking, cancellation, strict timeouts and saved artifacts. Passive-first; active scans require explicit consent.
3. Add Nuclei as a separate, constrained engine with template allowlists and output normalization; no arbitrary template execution exposed to the LLM.
4. Support a colleague's remote WireGuard VLAN with narrow routing and permitted HTTP target only. Revalidate that Docker egress reaches target without bridging VLANs broadly.
5. Incremental CVE intelligence collector from NVD, CISA KEV, FIRST EPSS, with structured ID lookup, deduplication, provenance and scheduled updates. Use a separate Chroma collection from the OWASP KB, and relational storage for authoritative version matching.
6. Correlate scanner findings, OWASP, CWE and real CVE/version evidence; generate reviewable PDF/JSON reports with observed vs inferred vs confirmed findings clearly separated.
