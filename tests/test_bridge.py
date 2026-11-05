"""Workspace Tool tests; ChromaDB and Ollama network requests are mocked."""
import asyncio
import importlib.util
import json
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "openwebui" / "tools" / "owasp_report_bridge.py"


def load_bridge():
    spec = importlib.util.spec_from_file_location("owasp_report_bridge_under_test", SOURCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_summary_uses_endpoint(monkeypatch):
    bridge = load_bridge()
    observed = []

    def fake_get(path, params=None):
        observed.append((path, params))
        return json.dumps({"distinct_alerts": 17})

    monkeypatch.setattr(bridge, "_agent_get", fake_get)
    result = asyncio.run(bridge.Tools().summarize_latest_zap_report())
    assert json.loads(result)["distinct_alerts"] == 17
    assert observed == [("/reports/latest/summary", None)]


def test_filter_severity_and_limit(monkeypatch):
    bridge = load_bridge()
    observed = []
    monkeypatch.setattr(bridge, "_agent_get", lambda path, params=None: observed.append((path, params)) or "{}")
    asyncio.run(bridge.Tools().list_zap_findings(severity="High", limit=10))
    assert observed == [("/reports/latest/findings", {"limit": 10, "severity": "High"})]
    err = asyncio.run(bridge.Tools().list_zap_findings(limit=200))
    assert json.loads(err)["status"] == "error"


def test_invalid_finding_id():
    bridge = load_bridge()
    err = asyncio.run(bridge.Tools().get_zap_finding(-1))
    assert json.loads(err)["status"] == "error"
