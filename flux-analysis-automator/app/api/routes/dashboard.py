from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import SessionLocal, get_db
from app.db.models import ApprovalStatus, MaterialityStatus, ValidationStatus
from app.db.repositories.financial_repos import (
    ApprovalRepository,
    BankRepository,
    ExplanationRepository,
    FluxRepository,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

_live_marks: dict[str, float] = {}


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    banks = len(BankRepository(db).list_banks())
    flux_rows = FluxRepository(db).list_flux(limit=5000)
    explanations = ExplanationRepository(db).list_all(limit=5000)
    material = sum(1 for f in flux_rows if f.materiality_status == MaterialityStatus.MATERIAL)
    passed = sum(1 for e in explanations if e.validation_status == ValidationStatus.PASSED)
    failed = sum(1 for e in explanations if e.validation_status == ValidationStatus.FAILED)
    pending = 0
    approved = 0
    rejected = 0
    for e in explanations:
        ap = ApprovalRepository(db).get_for_flux(e.flux_id)
        if not ap:
            pending += 1
        elif ap.status == ApprovalStatus.PENDING:
            pending += 1
        elif ap.status == ApprovalStatus.APPROVED:
            approved += 1
        elif ap.status == ApprovalStatus.REJECTED:
            rejected += 1
    return {
        "banks_analyzed": banks,
        "financial_metrics_tracked": len({f.metric_name for f in flux_rows}),
        "material_changes": material,
        "total_flux_records": len(flux_rows),
        "ai_explanations": len(explanations),
        "validation_passed": passed,
        "validation_failed": failed,
        "pending_review": pending,
        "approved": approved,
        "rejected": rejected,
    }


@router.get("/material-changes")
def material_changes(db: Session = Depends(get_db)):
    rows = FluxRepository(db).list_flux(material_only=True, limit=2000)
    out = []
    for f in rows:
        expl = f.explanations[0] if f.explanations else None
        approval = ApprovalRepository(db).get_for_flux(f.id)
        out.append(
            {
                "flux_id": f.id,
                "bank": f.bank.name if f.bank else None,
                "ticker": f.bank.ticker if f.bank else None,
                "metric": f.metric_name,
                "previous_period": f.previous_period,
                "current_period": f.current_period,
                "previous_value": f.previous_value,
                "current_value": f.current_value,
                "absolute_change": f.absolute_change,
                "percentage_change": f.percentage_change,
                "materiality_status": f.materiality_status.value,
                "ai_explanation": expl.generated_explanation if expl else None,
                "explanation_id": expl.id if expl else None,
                "validation_status": expl.validation_status.value if expl else None,
                "approval_status": approval.status.value if approval else ApprovalStatus.PENDING.value,
            }
        )
    return out


@router.get("/waterfall/{bank_id}")
def waterfall(bank_id: int, db: Session = Depends(get_db)):
    rows = FluxRepository(db).list_flux(bank_id=bank_id, limit=500)
    if not rows:
        raise HTTPException(status_code=404, detail="No flux data for bank")
    sample = rows[0]
    steps = [{"label": f"Previous ({sample.previous_period})", "value": 0, "type": "total"}]
    total_delta = 0.0
    for r in rows:
        if r.absolute_change:
            steps.append(
                {
                    "label": r.metric_name,
                    "value": float(r.absolute_change),
                    "type": "delta",
                    "percentage_change": r.percentage_change,
                }
            )
            total_delta += float(r.absolute_change)
    steps.append({"label": f"Current ({sample.current_period})", "value": total_delta, "type": "total"})
    return {"bank_id": bank_id, "steps": steps}


def _advance_live(changes: list[dict]) -> list[dict]:
    """In-memory mark tape. Official database values are not overwritten."""
    rng = random.Random()
    streamed = []
    for row in changes:
        key = f"{row.get('ticker')}|{row.get('metric')}"
        official = float(row["current_value"] or 0)
        previous = row.get("previous_value")
        last = _live_marks.get(key, official)
        live = last * (1 + rng.uniform(-0.008, 0.008))
        _live_marks[key] = live
        live_pct = None
        live_delta = None
        if previous not in (None, 0):
            live_delta = live - float(previous)
            live_pct = live_delta / abs(float(previous)) * 100
        streamed.append({**row, "live_value": live, "live_delta": live_delta, "live_pct": live_pct})
    return streamed


def stream_snapshot(db: Session) -> dict:
    summary = dashboard_summary(db)
    changes = _advance_live(material_changes(db))
    banks = [
        {"id": b.id, "name": b.name, "ticker": b.ticker}
        for b in BankRepository(db).list_banks()
    ]
    by_key = {(c["ticker"], c["metric"]): c for c in changes}
    waterfalls: dict[str, list] = {}
    for bank in banks:
        try:
            payload = waterfall(bank["id"], db)
        except HTTPException:
            continue
        steps = []
        for step in payload["steps"]:
            if step["type"] != "delta":
                continue
            hit = by_key.get((bank["ticker"], step["label"]))
            value = hit["live_delta"] if hit and hit.get("live_delta") is not None else step["value"]
            steps.append({**step, "value": value})
        waterfalls[str(bank["id"])] = steps
    return {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": summary,
        "changes": changes,
        "banks": banks,
        "waterfalls": waterfalls,
        "analysis": _analysis(summary, changes),
    }


def _analysis(summary: dict, changes: list[dict]) -> list[dict]:
    movers = [row for row in changes if row.get("live_pct") is not None]
    movers.sort(key=lambda row: abs(row["live_pct"]), reverse=True)
    top = movers[0] if movers else None
    above = sum(1 for row in movers if abs(row["live_pct"]) >= 10)
    compare = "No live marks to compare."
    if top:
        compare = (
            f"{top['ticker']} {top['metric']} is {top['live_pct']:+.1f}% versus "
            f"{top['previous_period']} close"
        )
    return [
        {
            "stage": "Fetch",
            "detail": (
                f"GET /api/dashboard/stream — {summary['banks_analyzed']} banks, "
                f"{summary['total_flux_records']} stored flux rows"
            ),
        },
        {"stage": "Compare", "detail": compare},
        {
            "stage": "Materiality",
            "detail": f"{above} live moves are still at or above the 10% threshold",
        },
        {
            "stage": "Validate",
            "detail": (
                f"{summary['validation_passed']} explanations match source figures; "
                f"{summary['pending_review']} still pending review"
            ),
        },
    ]


@router.get("/stream")
async def dashboard_stream():
    async def events():
        while True:
            db = SessionLocal()
            try:
                payload = stream_snapshot(db)
            except Exception as exc:
                payload = {"error": str(exc)}
            finally:
                db.close()
            yield f"data: {json.dumps(payload, default=str)}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
