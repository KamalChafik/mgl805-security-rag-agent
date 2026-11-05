"""
title: OWASP Report Bridge
author: Local Security Lab
version: 0.3.1
description: Read saved ZAP findings and search the OWASP knowledge collection.
"""

import asyncio
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Literal

# These values are evaluated within the Open WebUI container, not the FastAPI container.
SECURITY_AGENT_URL = os.getenv("SECURITY_AGENT_URL", "http://security-agent:8000").rstrip("/")
OLLAMA_URL = os.getenv("OLLAMA_URL") or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_URL = OLLAMA_URL.rstrip("/")
CHROMA_HOST = os.getenv("CHROMA_HTTP_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_HTTP_PORT", "8000"))
OWASP_COLLECTION_ID = os.getenv(
    "OWASP_COLLECTION_ID", ""
)
EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "qwen3-embedding:0.6b")


def _agent_get(path: str, params: dict | None = None) -> str:
    url = SECURITY_AGENT_URL + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.dumps(json.load(response), ensure_ascii=False)
    except urllib.error.HTTPError as exc:
        return json.dumps({"status": "error", "http_status": exc.code, "message": "Security Agent API request failed"})
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return json.dumps({"status": "error", "message": str(exc)})


def _embed(text: str) -> list[float]:
    request = urllib.request.Request(
        OLLAMA_URL + "/api/embed",
        data=json.dumps({"model": EMBEDDING_MODEL, "input": text}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)["embeddings"][0]


def _search_owasp(query: str) -> str:
    # Import only on actual use; this package is available in our Open WebUI container.
    import chromadb

    if not query.strip():
        return json.dumps({"status": "error", "message": "Query cannot be empty"})
    if not OWASP_COLLECTION_ID:
        return json.dumps({"status": "error", "message": "Set KNOWLEDGE_ID in .env and recreate Open WebUI before using OWASP search."})
    embedding = _embed(query[:500])
    chroma = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    collection = chroma.get_collection(OWASP_COLLECTION_ID)
    count = collection.count()
    if count == 0:
        return json.dumps({"status": "success", "matches": []})
    found = collection.query(
        query_embeddings=[embedding],
        n_results=min(3, count),
        include=["documents", "metadatas", "distances"],
    )
    matches = []
    for number, (document, metadata, distance) in enumerate(
        zip(found["documents"][0], found["metadatas"][0], found["distances"][0]), start=1
    ):
        meta = metadata or {}
        matches.append({
            "result_number": number,
            "source": meta.get("source_url") or meta.get("source") or meta.get("name") or "Unknown",
            "document_name": meta.get("name", "Unknown"),
            "distance": distance,
            "content": (document or "")[:1500],
        })
    return json.dumps({
        "status": "success",
        "query": query,
        "collection": OWASP_COLLECTION_ID,
        "total_collection_chunks": count,
        "matches_returned": len(matches),
        "matches": matches,
    }, ensure_ascii=False)


class Tools:
    async def summarize_latest_zap_report(self) -> str:
        """Retrieve ZAP report summary, counts by severity and top findings; scanner alerts are not confirmed vulnerabilities."""
        return await asyncio.to_thread(_agent_get, "/reports/latest/summary")

    async def list_zap_findings(
        self,
        severity: Literal["All", "High", "Medium", "Low", "Informational"] = "All",
        limit: int = 20,
    ) -> str:
        """List saved ZAP findings by severity. Use finding_id from the returned list for detailed inspection."""
        if not 1 <= limit <= 50:
            return json.dumps({"status": "error", "message": "limit must be between 1 and 50"})
        params = {"limit": limit}
        if severity != "All":
            params["severity"] = severity
        return await asyncio.to_thread(_agent_get, "/reports/latest/findings", params)

    async def get_zap_finding(self, finding_id: int) -> str:
        """Retrieve evidence, CWE, URLs, parameter and remediation for an existing ZAP alert; not independently validated."""
        if finding_id < 0:
            return json.dumps({"status": "error", "message": "finding_id must be nonnegative"})
        return await asyncio.to_thread(_agent_get, f"/reports/latest/findings/{finding_id}")

    async def search_owasp_knowledge(self, query: str) -> str:
        """Search indexed OWASP passages via Ollama embeddings and ChromaDB. Cite only retrieved sources."""
        try:
            return await asyncio.to_thread(_search_owasp, query)
        except Exception as exc:
            return json.dumps({"status": "error", "message": f"OWASP retrieval unavailable: {exc}"})
