#!/usr/bin/env python3
"""Verify the external Windows Ollama server and required installed models."""
from __future__ import annotations
import json
import urllib.error
import urllib.request
from _common import load_env


def main():
    env = load_env()
    url = env.get('OLLAMA_URL', '').rstrip('/')
    if not url:
        raise SystemExit('Missing OLLAMA_URL in .env')
    for path in ('/api/tags', '/api/ps'):
        try:
            with urllib.request.urlopen(url + path, timeout=8) as response:
                data = json.load(response)
            print(path, 'OK')
            if path == '/api/tags':
                models = sorted(x.get('name', '?') for x in data.get('models', []))
                print('Installed:', ', '.join(models) if models else '(none)')
                for name in (env.get('LLM_MODEL', 'qwen3.5:9b'), env.get('EMBEDDING_MODEL', 'qwen3-embedding:0.6b')):
                    print(f'  {name}:', 'FOUND' if name in models else 'MISSING')
            else:
                print('Loaded in memory:', ', '.join(x.get('name', '?') for x in data.get('models', [])) or '(none)')
        except (urllib.error.URLError, OSError, TimeoutError, ValueError) as error:
            raise SystemExit(f'Cannot connect to Ollama {url}: {error}')

if __name__ == '__main__':
    main()
