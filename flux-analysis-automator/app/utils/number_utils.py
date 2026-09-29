from __future__ import annotations

import re
from typing import Iterable

_NUMBER_PATTERN = re.compile(
    r"""
    (?<!\w)
    (\$?\s*-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:[Bb]|bn|billion|M|mn|million|K|k)?)
    (?!\w)
    """,
    re.VERBOSE,
)

_PCT_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*%")


def parse_numeric_token(token: str) -> float | None:
    cleaned = token.strip().replace("$", "").replace(",", "").replace(" ", "")
    if not cleaned:
        return None
    multiplier = 1.0
    lower = cleaned.lower()
    if lower.endswith("billion") or lower.endswith("bn") or (lower.endswith("b") and not lower.endswith("mb")):
        cleaned = re.sub(r"(?i)(billion|bn|b)$", "", cleaned)
        multiplier = 1_000_000_000
    elif lower.endswith("million") or lower.endswith("mn") or lower.endswith("m"):
        cleaned = re.sub(r"(?i)(million|mn|m)$", "", cleaned)
        multiplier = 1_000_000
    elif lower.endswith("k"):
        cleaned = cleaned[:-1]
        multiplier = 1_000
    try:
        return float(cleaned) * multiplier
    except ValueError:
        return None


def extract_numbers(text: str) -> list[float]:
    values: list[float] = []
    for match in _NUMBER_PATTERN.finditer(text):
        val = parse_numeric_token(match.group(1))
        if val is not None:
            values.append(val)
    return values


def extract_percentages(text: str) -> list[float]:
    return [float(m.group(1)) for m in _PCT_PATTERN.finditer(text)]


def value_matches_allowed(candidate: float, allowed: Iterable[float], rel_tol: float = 0.015) -> bool:
    for a in allowed:
        if a is None:
            continue
        denom = max(abs(a), 1.0)
        if abs(candidate - a) / denom <= rel_tol:
            return True
    return False
