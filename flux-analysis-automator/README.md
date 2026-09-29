# Flux Analysis Automator

Compares the latest quarter with the previous quarter for six banks (JPM, BAC, WFC, C, GS, MS). It flags material changes, writes a short explanation, checks that every number in that text matches the database, and waits for a person to approve it.

## Run

```bash
cd "/home/parth/Financial Analytics Proj/flux-analysis-automator"
source "../.venv/bin/activate"
export PYTHONPATH="$PWD"

docker compose up -d db
alembic upgrade head
python scripts/run_pipeline.py
uvicorn app.main:app --port 8001
```

Open **http://127.0.0.1:8001/ui**

The page keeps calling the API and updating the charts. Approve or reject a row on the dashboard.

API docs: **http://127.0.0.1:8001/docs**

## Optional

Put a Groq key in `.env` as `GROQ_API_KEY=` and set `LLM_PROVIDER=groq`. Without a key, the app uses a short template and still checks the numbers.

Power BI (Windows only): see `powerbi/README.md`.
