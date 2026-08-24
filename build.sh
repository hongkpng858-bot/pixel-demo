#!/usr/bin/env bash
# Regenerate every animation + run QA. Only deps: python3 + Pillow.
set -euo pipefail
cd "$(dirname "$0")"
python3 make_slime.py
python3 make_walker.py
python3 make_dog.py
python3 make_robot.py
python3 make_knight.py
python3 make_bird.py
python3 make_serpent.py
python3 make_fish.py
python3 make_bug.py
python3 make_ghost.py
python3 verify.py
echo "== build OK =="
