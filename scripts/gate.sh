#!/usr/bin/env bash
# The quality gate, with exit codes that actually propagate.
#
# Piping ruff through `tail` swallows its status and lets a red build commit,
# which happened twice before this script existed.
set -euo pipefail

PY=.venv/Scripts/python.exe
[ -x "$PY" ] || PY=.venv/bin/python

echo "== ruff (lint) ==";   "$PY" -m ruff check . --output-format=concise
echo "== ruff (format) =="; "$PY" -m ruff format --check . >/dev/null && echo "formatted"
echo "== mypy ==";          "$PY" -m mypy
echo "== pytest ==";        "$PY" -m pytest -q
echo
echo "gate: all green"
