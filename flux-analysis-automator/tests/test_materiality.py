from app.utils.financial_utils import evaluate_materiality


def test_not_material_below_pct():
    result = evaluate_materiality(5_000_000, 9.0, True, "Net Revenue")
    assert result.status == "NOT_MATERIAL"


def test_material_when_both_thresholds_exceeded():
    result = evaluate_materiality(150_000_000, 15.0, True, "Net Revenue")
    assert result.status == "MATERIAL"


def test_undefined_without_percentage():
    result = evaluate_materiality(100, None, False)
    assert result.status == "UNDEFINED"
