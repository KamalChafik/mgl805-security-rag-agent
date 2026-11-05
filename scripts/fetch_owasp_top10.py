#!/usr/bin/env python3
"""Download official OWASP Top 10:2025 English markdown files (A01...A10)."""
from __future__ import annotations
import argparse
import json
import re
import urllib.request
from pathlib import Path
from _common import ROOT

API = 'https://api.github.com/repos/OWASP/Top10/contents/2025/docs/en'
PATTERN = re.compile(r'^A(0[1-9]|10)_2025-.*\.md$')


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': 'mgl805-owasp-loader/1.0', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'knowledge/owasp-top10-2025')
    parser.add_argument('--overwrite', action='store_true', help='Replace existing files with upstream versions')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    items = json.loads(get(API))
    files = sorted((i for i in items if PATTERN.fullmatch(i.get('name', ''))), key=lambda i: i['name'])
    if len(files) != 10:
        raise SystemExit(f'Expected 10 OWASP 2025 chapter files; GitHub API returned {len(files)}. No download attempted.')
    for info in files:
        dst = args.output / info['name']
        if dst.exists() and not args.overwrite:
            print(f'SKIP {dst.name} (use --overwrite to refresh)')
            continue
        source = info.get('download_url')
        if not source:
            raise SystemExit(f"No official download URL for {info['name']}")
        body = get(source)
        if not body.strip() or len(body) < 100:
            raise SystemExit(f'Unexpectedly small source file: {info["name"]}')
        dst.write_bytes(body)
        print(f'SAVED {dst.name} ({len(body)} bytes)')
    print('Official source: https://github.com/OWASP/Top10/tree/master/2025/docs/en')

if __name__ == '__main__':
    main()
