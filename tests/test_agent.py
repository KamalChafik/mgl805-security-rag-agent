"""API regression tests using synthetic input only: no live scanning."""
import importlib.util
import json
from pathlib import Path

from fastapi.testclient import TestClient

SOURCE = Path(__file__).resolve().parents[1] / "services" / "security-agent" / "main.py"
FIXTURE = Path(__file__).parent / "fixtures" / "synthetic-zap.json"


def setup_client(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("security_agent_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "test-report.json").write_text(FIXTURE.read_text(), encoding="utf-8")
    monkeypatch.setattr(module, "REPORT_DIR", tmp_path)
    return TestClient(module.app)


def test_summary(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    data = client.get("/reports/latest/summary").json()
    assert data["distinct_alerts"] == 2
    assert data["severity_counts"] == {"High": 1, "Medium": 0, "Low": 1, "Informational": 0}
    assert data["affected_instances"] == 2
    assert data["top_findings"][0]["cwe_id"] == "CWE-89"
    assert data["top_findings"][0]["scanner_confidence"] in ("Medium", "Unknown")


def test_filter_and_detail(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    data = client.get("/reports/latest/findings", params={"severity": "High"}).json()
    assert data["total_matches"] == 1
    finding_id = data["findings"][0]["finding_id"]
    finding = client.get(f"/reports/latest/findings/{finding_id}").json()
    assert finding["risk"] == "High"
    assert finding["verification"] == "Not independently validated"
    assert finding["instances_detail"][0]["parameter"] == "username"
    assert client.get("/reports/latest/findings/999").status_code == 404


def test_no_reports(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    for path in tmp_path.glob("*.json"):
        path.unlink()
    assert client.get("/reports/latest/summary").status_code == 404


def test_bad_limit(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    assert client.get("/reports/latest/findings?limit=99").status_code == 422
