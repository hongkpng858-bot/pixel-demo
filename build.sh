#!/usr/bin/env bash
# Regenerate every animation + run QA. Only deps: python3 + Pillow.
set -euo pipefail
cd "$(dirname "$0")"
python3 make_slime.py
python3 make_walker.py
python3 verify.py
echo "== build OK =="
