# Power BI dashboard specification

Power BI Desktop (Windows) is the analytics UI. Connect with **Get data → Web** to the URLs in `README.md`.

## Page 1 — Executive Overview

**Visuals**

- KPI cards: `banks_analyzed`, `material_changes`, `pending_review`, `approved`
- Clustered bar: material changes by `ticker`
- Validation mix: `validation_passed` vs `validation_failed`

**Data:** `GET /api/dashboard/summary`, `GET /api/dashboard/material-changes`

---

## Page 2 — Flux Analysis

**Table**

Bank | Metric | Previous | Current | Absolute Change | % Change | Materiality

**Filters:** bank, period, metric, materiality_status, approval_status

**Data:** `GET /api/dashboard/material-changes`

---

## Page 3 — Variance Waterfall

**Visual:** Waterfall on `steps` from `GET /api/dashboard/waterfall/{bank_id}`

Use `type = delta` as the change bars. Slicer: `bank_id` from `GET /api/banks` (Wells Fargo is **3**).

---

## Page 4 — Needs Explanation

**Table:** Bank, Metric, Previous Value, Current Value, % Change, Absolute Change, AI Explanation, Validation Status, Approval Status

**Filter:** `approval_status = PENDING` and `materiality_status = MATERIAL`

**Data:** `GET /api/dashboard/material-changes`

---

## Page 5 — AI Control / Validation

**KPIs:** ai_explanations, validation_passed, validation_failed, pending_review, approved, rejected

**Data:** `GET /api/dashboard/summary`, `GET /api/explanations`

---

## DAX

```dax
Material Change Count = COUNTROWS('material-changes')

Pending Review =
CALCULATE(COUNTROWS('material-changes'), 'material-changes'[approval_status] = "PENDING")
```
