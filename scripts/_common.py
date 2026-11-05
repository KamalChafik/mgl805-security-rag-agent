"""Shared CLI helpers. Never print API keys or DB passwords."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env() -> dict[str, str]:
    data: dict[str, str] = {}
    path = ROOT / '.env'
    if path.is_file():
        for raw in path.read_text(encoding='utf-8').splitlines():
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
    data.update(os.environ)
    return data


def need(value: str | None, label: str) -> str:
    if not value:
        raise SystemExit(f"Missing {label}. Set it in .env or your environment.")
    return value


def webui_url(config: dict[str, str]) -> str:
    # The host-side UI URL differs from Docker's internal port.
    bind_ip = config.get('BIND_IP', '127.0.0.1')
    if bind_ip == '0.0.0.0':
        bind_ip = '127.0.0.1'
    return config.get('OPENWEBUI_URL') or f"http://{bind_ip}:{config.get('WEBUI_PORT', '3000')}"
