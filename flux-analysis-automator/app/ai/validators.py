from __future__ import annotations

from app.utils.number_utils import extract_numbers, extract_percentages, value_matches_allowed


def validate_explanation_numbers(
    explanation_text: str,
    allowed_values: list[float],
    allowed_percentages: list[float],
) -> tuple[bool, list[str]]:
    errors: list[str] = []
    nums = extract_numbers(explanation_text)
    pcts = extract_percentages(explanation_text)

    for n in nums:
        if allowed_percentages and value_matches_allowed(n, allowed_percentages, rel_tol=0.05):
            continue
        if not value_matches_allowed(n, allowed_values):
            errors.append(f"Unsupported numeric value in explanation: {n:,.2f}")

    for p in pcts:
        if allowed_percentages and not value_matches_allowed(p, allowed_percentages, rel_tol=0.05):
            errors.append(f"Unsupported percentage in explanation: {p}%")

    return len(errors) == 0, errors
