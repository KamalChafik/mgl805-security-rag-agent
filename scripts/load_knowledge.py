#!/usr/bin/env python3
"""Upload OWASP files through Open WebUI's API, poll processing, then link to knowledge.

This intentionally DOES NOT write vectors directly into ChromaDB: Open WebUI
chunks documents and calls Ollama for embeddings while indexing into ChromaDB.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit('Missing requests; run ./scripts/install-tools.sh')
from _common import ROOT, load_env, need, webui_url


def process_one(session, base, knowledge_id, path, seconds):
    with path.open('rb') as file:
        r = session.post(f'{base}/api/v1/files/', files={'file': (path.name, file, 'text/markdown')}, timeout=90)
    r.raise_for_status()
    file_id = r.json().get('id')
    if not file_id:
        raise RuntimeError(f'Upload returned no file ID for {path.name}')
    print(f'  uploaded file id={file_id} (waiting for processing)')
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        status_r = session.get(f'{base}/api/v1/files/{file_id}/process/status', timeout=25)
        status_r.raise_for_status()
        info = status_r.json()
        status = info.get('status', '')
        if status == 'completed':
            break
        if status == 'failed':
            raise RuntimeError(f"Open WebUI processing failed: {info.get('error', info)}")
        time.sleep(3)
    else:
        raise TimeoutError(f'File processing not completed within {seconds}s (id={file_id})')
    r = session.post(f'{base}/api/v1/knowledge/{knowledge_id}/file/add', json={'file_id': file_id}, timeout=120)
    if r.status_code not in (200, 201):
        # Inform caller rather than silently treating duplicate/failed add as success.
        raise RuntimeError(f'Knowledge add HTTP {r.status_code}: {r.text[:400]} (uploaded file id={file_id})')
    return file_id


def main():
    env = load_env()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=ROOT / 'knowledge/owasp-top10-2025')
    p.add_argument('--knowledge-id', default=env.get('KNOWLEDGE_ID', ''))
    p.add_argument('--url', default=webui_url(env))
    p.add_argument('--timeout', type=int, default=600, help='Max processing time per file in seconds')
    p.add_argument('--force', action='store_true', help='Retry even if local manifest says previously uploaded')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    base = args.url.rstrip('/')
    kb = need(args.knowledge_id, 'KNOWLEDGE_ID (created in Open WebUI)')
    files = sorted(args.source.glob('*.md'))
    if not files:
        raise SystemExit(f'No .md files in {args.source}; run python3 scripts/fetch_owasp_top10.py')
    state_path = ROOT / 'data/state/knowledge_uploads.json'
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    token = env.get('OPENWEBUI_API_KEY', '').strip()
    if not args.dry_run:
        need(token, 'OPENWEBUI_API_KEY (create it under Open WebUI Settings > Account)')
    session = requests.Session()
    if token:
        session.headers['Authorization'] = f'Bearer {token}'
    session.headers['Accept'] = 'application/json'
    failures = 0
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        key = f'{base}|{kb}|{path.resolve()}|{digest}'
        if key in state and not args.force:
            print(f'SKIP {path.name}: already uploaded according to local manifest')
            continue
        if args.dry_run:
            print(f'DRY RUN {path.name}: would upload to KB {kb}')
            continue
        print(f'PROCESS {path.name}')
        try:
            file_id = process_one(session, base, kb, path, args.timeout)
        except (requests.RequestException, RuntimeError, TimeoutError) as exc:
            print(f'ERROR {path.name}: {exc}', file=sys.stderr)
            failures += 1
            continue
        state[key] = {'file_id': file_id, 'sha256': digest, 'name': path.name}
        state_path.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
        print(f'  LINKED to knowledge {kb}')
    print(f'Finished. Files inspected: {len(files)}; errors: {failures}')
    if failures:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
