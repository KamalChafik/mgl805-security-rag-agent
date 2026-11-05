#!/usr/bin/env python3
"""Validate a ZAP JSON report, then copy it into data/reports for read-only FastAPI."""
from __future__ import annotations
import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from _common import ROOT


def validate(doc):
    if not isinstance(doc, dict) or not isinstance(doc.get('site'), list):
        raise ValueError("Expected ZAP JSON report with a top-level 'site' list")
    count = sum(len(x.get('alerts', [])) for x in doc['site'] if isinstance(x, dict))
    return count


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path, help='JSON report exported by ZAP')
    p.add_argument('--name', help='Optional safe destination filename (basename only)')
    args = p.parse_args()
    src = args.source.resolve(strict=True)
    data = json.loads(src.read_text(encoding='utf-8'))
    alerts = validate(data)
    filename = args.name or f'{datetime.now().strftime("%Y%m%d-%H%M%S")}-{src.name}'
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*\.json', filename) or filename.startswith('.'):
        raise SystemExit('Destination name must be a safe *.json basename (no folders or spaces).')
    dest_dir = ROOT / 'data/reports'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    if dest.exists():
        raise SystemExit(f'Already exists: {dest} (choose a different --name)')
    shutil.copy2(src, dest)
    dest.chmod(0o644)  # read by the unprivileged FastAPI container user
    print(f'COPIED {dest}\nAlert types: {alerts}. FastAPI reads the newest JSON report by file modification time.')
    print('WARNING: ZAP reports can contain sensitive parameters or evidence; do not commit or share them publicly.')

if __name__ == '__main__':
    main()
