#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [[ -x .venv/bin/python ]]; then .venv/bin/python -m pytest -q; else python3 -m pytest -q; fi
