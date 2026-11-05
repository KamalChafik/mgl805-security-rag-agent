#!/usr/bin/env python3
"""Summarize existing on-disk ZAP JSON without contacting a scanner or running scans."""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
from _common import ROOT
from import_zap_report import validate
RISK = {'3':'High','2':'Medium','1':'Low','0':'Informational'}


def summarize(path: Path):
    doc = json.loads(path.read_text(encoding='utf-8'))
    n = validate(doc)
    alerts = [a for site in doc['site'] if isinstance(site, dict) for a in site.get('alerts', []) if isinstance(a, dict)]
    counts = Counter(RISK.get(str(a.get('riskcode')), 'Informational') for a in alerts)
    print('Report:', path)
    print('Version:', doc.get('@version', 'unknown'))
    print('Distinct alerts:', n)
    print('Affected instances:', sum(len(a.get('instances', [])) for a in alerts))
    for sev in ('High','Medium','Low','Informational'):
        print(f'  {sev}: {counts[sev]}')
    print('Alerts require independent validation before being called confirmed vulnerabilities.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('report', nargs='?', type=Path, help='Optional report path; otherwise latest in data/reports')
    a=p.parse_args()
    paths=sorted((ROOT/'data/reports').glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    path=a.report if a.report else (paths[0] if paths else None)
    if path is None:
        raise SystemExit('No reports found. Export a ZAP JSON report into data/reports/')
    summarize(path)

if __name__=='__main__':main()
