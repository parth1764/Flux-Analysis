from __future__ import annotations

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def fetch_sec_company_facts(cik: str) -> dict | None:
    """Optional SEC XBRL company facts (metadata only in Phase 2 — enrichment hook)."""
    settings = get_settings()
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json"
    headers = {"User-Agent": settings.sec_user_agent, "Accept": "application/json"}
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("SEC fetch failed for CIK %s: %s", cik, exc)
        return None
