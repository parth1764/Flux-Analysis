#!/usr/bin/env bash
# Use project venv — do NOT run with conda base (missing psycopg2, alembic).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${ROOT}/../.venv"

if [[ ! -d "$VENV" ]]; then
  python3 -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -q -r "$ROOT/requirements.txt"

if [[ ! -f "$ROOT/.env" ]]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
fi

export PYTHONPATH="$ROOT"
echo "Ready. Run:"
echo "  source \"$VENV/bin/activate\""
echo "  export PYTHONPATH=\"$ROOT\""
echo "  cd \"$ROOT\""
echo "  docker compose up -d db"
echo "  alembic upgrade head"
echo "  python scripts/run_pipeline.py"
echo "  uvicorn app.main:app --reload --port 8001"
