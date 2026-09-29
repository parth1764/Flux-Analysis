from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings


@dataclass(frozen=True)
class FluxResult:
    absolute_change: float | None
    percentage_change: float | None
    percentage_change_defined: bool


def calculate_flux(previous: float | None, current: float | None) -> FluxResult:
    if previous is None or current is None:
        return FluxResult(None, None, False)
    absolute = current - previous
    if previous == 0:
        return FluxResult(absolute, None, False)
    pct = (absolute / abs(previous)) * 100.0
    return FluxResult(absolute, pct, True)


@dataclass(frozen=True)
class MaterialityResult:
    status: str
    reason: str


def evaluate_materiality(
    absolute_change: float | None,
    percentage_change: float | None,
    percentage_defined: bool,
    normalized_metric: str | None = None,
) -> MaterialityResult:
    settings = get_settings()
    pct_threshold = settings.materiality_pct_threshold
    abs_threshold = settings.materiality_absolute_threshold

    overrides = settings.materiality_metric_overrides()
    if normalized_metric and normalized_metric in overrides:
        pct_threshold = overrides[normalized_metric].get("pct", pct_threshold)
        abs_threshold = overrides[normalized_metric].get("absolute", abs_threshold)

    if absolute_change is None or not percentage_defined or percentage_change is None:
        return MaterialityResult(
            "UNDEFINED",
            "Insufficient period data to evaluate materiality.",
        )

    abs_amt = abs(absolute_change)
    abs_pct = abs(percentage_change)

    if abs_pct >= pct_threshold and abs_amt >= abs_threshold:
        return MaterialityResult(
            "MATERIAL",
            f"Percentage change {percentage_change:.2f}% exceeded {pct_threshold}% "
            f"and absolute change {absolute_change:,.0f} exceeded {abs_threshold:,.0f}.",
        )
    return MaterialityResult(
        "NOT_MATERIAL",
        f"Change below thresholds ({pct_threshold}% and {abs_threshold:,.0f}).",
    )


def period_sort_key(period: str) -> tuple[int, int]:
    """Sort key for labels like 2025-Q1 or 2025-FY."""
    if "-Q" in period:
        year_s, q_s = period.split("-Q")
        return int(year_s), int(q_s)
    if "-FY" in period:
        return int(period.replace("-FY", "")), 5
    return 0, 0
