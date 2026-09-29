# Power BI data contract

Base URL: `http://127.0.0.1:8001/api`

All responses are JSON. In Power BI Desktop use **Get data → Web**.

---

## GET /api/dashboard/summary

**Purpose:** Executive KPI cards (Page 1 and Page 5).

| Field | Type | Description |
|-------|------|-------------|
| banks_analyzed | int | Count of banks |
| financial_metrics_tracked | int | Distinct metrics in the flux table |
| material_changes | int | MATERIAL flux rows |
| total_flux_records | int | All flux rows |
| ai_explanations | int | Generated explanations |
| validation_passed | int | PASSED validation |
| validation_failed | int | FAILED validation |
| pending_review | int | Approval PENDING |
| approved | int | Human approved |
| rejected | int | Human rejected |

---

## GET /api/dashboard/material-changes

**Purpose:** Flux table plus AI narrative (Pages 2 and 4).

| Field | Type |
|-------|------|
| flux_id | int |
| bank | string |
| ticker | string |
| metric | string |
| previous_period | string |
| current_period | string |
| previous_value | number |
| current_value | number |
| absolute_change | number |
| percentage_change | number |
| materiality_status | string |
| ai_explanation | string |
| validation_status | string |
| approval_status | string |

`percentage_change` is already in percent points (23.0 means 23%). Format the column as a decimal, not Power BI’s default percent.

---

## GET /api/dashboard/waterfall/{bank_id}

**Purpose:** Waterfall chart (Page 3).

| Field | Type |
|-------|------|
| bank_id | int |
| steps | array |
| steps[].label | string |
| steps[].value | number |
| steps[].type | `total` or `delta` |

Bank ids: 1 JPM, 2 BAC, 3 WFC, 4 C, 5 GS, 6 MS.

---

## GET /api/flux/material

Material-only flux rows. Same core fields as the OpenAPI `FluxOut` schema.

---

## GET /api/explanations/pending

Items awaiting human review.

---

## POST /api/ingestion/pipeline

Full refresh before a Power BI dataset refresh. Returns ingestion, flux, and explanation counts.

---

## Refresh order

1. `POST /api/ingestion/pipeline` (or leave current data if you only approved a row)
2. Refresh the Power BI dataset
3. Controllers approve via `POST /api/explanations/{id}/approve`
