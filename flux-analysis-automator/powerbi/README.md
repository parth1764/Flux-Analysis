# Power BI

- [Data dictionary](data_dictionary.md) — API fields for the Web connector
- [Dashboard specification](dashboard_specification.md) — 5-page layout

Keep the API running (`uvicorn` on port **8001**), then in Power BI Desktop on Windows: **Get data → Web**.

| Page | URL |
|------|-----|
| Executive KPIs | `http://127.0.0.1:8001/api/dashboard/summary` |
| Flux + AI review | `http://127.0.0.1:8001/api/dashboard/material-changes` |
| Waterfall (Wells Fargo) | `http://127.0.0.1:8001/api/dashboard/waterfall/3` |
| Banks | `http://127.0.0.1:8001/api/banks` |

Power BI Desktop is Windows-only. The Linux machine already serves the data; build the `.pbix` on a Windows PC or a Windows VM pointed at this API.

Refresh the warehouse first if needed: `POST http://127.0.0.1:8001/api/ingestion/pipeline`
