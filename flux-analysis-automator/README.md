# Flux Analysis Automator

Automates **month-end / quarter-end flux analysis** for global banks: ingest **public financials**, compute **period-over-period variance**, apply **configurable materiality**, generate **LLM explanations** from verified facts only, **validate every number** in AI text, route through **human approval**, and serve **Power BI–ready REST APIs**.

Coexists with the **fincontrol** valuation-control project in the parent folder.

---

## Problem

Controllers and FP&A teams spend days building flux decks answering **“why did this number change?”** Manual work is error-prone; unchecked AI drafts can cite numbers that never appeared in source data.

---

## Solution

```
yFinance (+ optional SEC metadata)
        ↓
Ingestion & normalization (6 banks)
        ↓
PostgreSQL (source of truth)
        ↓
Flux + materiality engines
        ↓
LLM narrative (structured JSON, facts-only prompt)
        ↓
Deterministic number validator
        ↓
Human approval (PENDING → APPROVED / REJECTED)
        ↓
FastAPI → Power BI
```

---

## Features

- **6 banks:** JPM, BAC, WFC, C, GS, MS  
- **Normalized metrics:** assets, NII, revenue, net income, loans, deposits, etc.  
- **Idempotent ETL** (upsert by bank / period / metric)  
- **Safe % change** when prior period is zero  
- **Materiality:** configurable % + absolute thresholds (per-metric overrides)  
- **AI governance:** validation gate before approval  
- **No Streamlit** — open **http://127.0.0.1:8001/ui** on Linux; Power BI uses the same API on Windows  

---

## Tech stack

Python 3.11+, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Docker Compose, yFinance, OpenAI/Gemini (optional), pytest.

---

## Quick start

```bash
cd "/home/parth/Financial Analytics Proj/flux-analysis-automator"
cp .env.example .env
# Optional: set OPENAI_API_KEY or GEMINI_API_KEY in .env

docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python scripts/run_pipeline.py
```

- **Dashboard:** http://127.0.0.1:8001/ui  
- **Swagger:** http://127.0.0.1:8001/docs  
- **Health:** http://127.0.0.1:8001/api/health  
- **Executive KPIs:** http://127.0.0.1:8001/api/dashboard/summary  

### Local (Postgres in Docker, API on host)

```bash
docker compose up -d db
source ../.venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$PWD"
alembic upgrade head
uvicorn app.main:app --reload --port 8001
python scripts/run_pipeline.py
```

Then open **http://127.0.0.1:8001/ui**. Approve or reject a material row there. Power BI (Windows) can use the same API later; see `powerbi/README.md`.

```bash
pytest
```

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `LLM_API_KEY` / `OPENAI_API_KEY` | Optional LLM (template mode if empty) |
| `LLM_PROVIDER` | `openai` or `gemini` |
| `MATERIALITY_PCT_THRESHOLD` | Default 10% |
| `MATERIALITY_ABSOLUTE_THRESHOLD` | Default 100000000 |
| `SEC_USER_AGENT` | SEC API (future enrichment) |

---

## API highlights

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/ingestion/pipeline` | Full refresh |
| GET | `/api/flux/material` | Material variances |
| POST | `/api/explanations/generate` | AI + validation |
| GET | `/api/explanations/pending` | Review queue |
| POST | `/api/explanations/{id}/approve` | Human approve (requires validation PASSED) |
| GET | `/api/dashboard/summary` | Power BI KPIs |
| GET | `/api/dashboard/material-changes` | Flux + AI table |
| GET | `/api/dashboard/waterfall/{bank_id}` | Waterfall data |

Full contract: `powerbi/data_dictionary.md`

---

## Power BI

See `powerbi/README.md` and `powerbi/dashboard_specification.md`. Power BI Desktop is Windows-only.

On Linux, open the HTML dashboard while the API is running:

**http://127.0.0.1:8001/ui**

---

## AI safety

1. Database holds all figures.  
2. LLM receives a **JSON fact pack** only.  
3. **Validator** rejects narratives citing numbers not in the fact pack.  
4. **Approval** is never automatic; failed validation cannot be approved.  

---

## Tests

```bash
cd flux-analysis-automator
PYTHONPATH=. pytest
```

**15 tests** — flux math, materiality, AI validation, API, ingestion (mocked).

---

## Example workflow

1. `python scripts/run_pipeline.py`  
2. Open `/api/dashboard/material-changes`  
3. Review `/api/explanations/pending`  
4. `POST .../approve` with reviewer email  
5. Refresh the Power BI dataset  

---

## Future improvements

- Deeper SEC XBRL line-item mapping  
- Scheduled ingestion (Airflow)  
- RBAC and audit trail  
- Model monitoring / prompt versioning dashboard  

---

## License

MIT — portfolio and learning use.
