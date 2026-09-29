"""Maps vendor line items to normalized financial taxonomy."""

from __future__ import annotations

NORMALIZED_METRICS: dict[str, list[str]] = {
    "Total Assets": ["Total Assets", "Total Assets"],
    "Total Liabilities": ["Total Liabilities Net Minority Interest", "Total Liabilities"],
    "Total Equity": ["Stockholders Equity", "Total Equity Gross Minority Interest", "Common Stock Equity"],
    "Net Interest Income": ["Net Interest Income"],
    "Net Revenue": ["Total Revenue", "Operating Revenue", "Revenue"],
    "Net Income": ["Net Income", "Net Income Common Stockholders", "Net Income Including Noncontrolling Interests"],
    "Operating Expenses": ["Operating Expense", "Total Operating Expenses As Reported"],
    "Provision for Credit Losses": ["Provision For Doubtful Accounts", "Credit Losses Provision"],
    "Loans": ["Net Loan", "Loans And Leases", "Total Loans"],
    "Deposits": ["Deposits", "Total Deposits"],
    "Cash": ["Cash And Cash Equivalents", "Cash Cash Equivalents And Federal Funds Sold"],
    "Securities": ["Available For Sale Securities", "Trading Securities", "Investment Securities"],
    "Goodwill": ["Goodwill", "Goodwill And Other Intangible Assets"],
}


def normalize_metric_name(source_label: str) -> str | None:
    label = source_label.strip()
    for normalized, aliases in NORMALIZED_METRICS.items():
        if label in aliases or label == normalized:
            return normalized
        for alias in aliases:
            if alias.lower() == label.lower():
                return normalized
    return None
