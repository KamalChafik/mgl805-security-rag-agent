#!/usr/bin/env python3
"""List ChromaDB collections and optionally verify Ollama embedding similarity search.

Runs *inside the Open WebUI container*, which already includes chromadb.
Do not publish the ChromaDB API on your LAN.
"""
from __future__ import annotations
import argparse
import subprocess
import sys

CODE = r'''
import json, os, sys, urllib.request
import chromadb
host = os.getenv('CHROMA_HTTP_HOST', 'chromadb')
port = int(os.getenv('CHROMA_HTTP_PORT', '8000'))
collection_id = os.getenv('OWASP_COLLECTION_ID', '').strip()
client = chromadb.HttpClient(host=host, port=port)
query = sys.argv[1] if len(sys.argv) > 1 else ''
print('Chroma heartbeat:', client.heartbeat())
collections = client.list_collections()
for c in collections:
    name = c if isinstance(c, str) else c.name
    print('COLLECTION:', name, '| chunks:', client.get_collection(name).count())
if not collection_id:
    print('NOTE: KNOWLEDGE_ID is not configured yet; create KB in Open WebUI.')
    sys.exit(0)
col = client.get_collection(collection_id)
print('Configured OWASP collection:', collection_id, '| chunks:', col.count())
if query:
    url = os.environ['OLLAMA_BASE_URL'].rstrip('/') + '/api/embed'
    model = os.environ['RAG_EMBEDDING_MODEL']
    req = urllib.request.Request(url, data=json.dumps({'model':model,'input':query}).encode(), headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=60) as res:
        vector = json.load(res)['embeddings'][0]
    print('Embedding dimensions:', len(vector))
    result = col.query(query_embeddings=[vector], n_results=min(3, col.count()), include=['documents','metadatas','distances']) if col.count() else None
    if result:
        for i, (text, meta) in enumerate(zip(result['documents'][0], result['metadatas'][0]), 1):
            print('Result', i, '| source:', (meta or {}).get('source_url') or (meta or {}).get('source') or 'unknown')
            print((text or '')[:350].replace('\n', ' '))
'''

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--query', default='', help='Optional test query e.g. SQL injection CWE-89')
    args = p.parse_args()
    cmd = ['docker', 'compose', 'exec', '-T', 'open-webui', 'python', '-c', CODE, args.query]
    print('Checking Chroma through the running Open WebUI container ...', flush=True)
    return subprocess.call(cmd)

if __name__ == '__main__':
    sys.exit(main())
