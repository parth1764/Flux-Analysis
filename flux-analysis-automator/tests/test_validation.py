from app.ai.validators import validate_explanation_numbers


def test_validation_passes_correct_numbers():
    text = "Net interest income increased from $10.0B to $11.5B, a 15% increase."
    ok, errors = validate_explanation_numbers(
        text,
        allowed_values=[10_000_000_000, 11_500_000_000, 1_500_000_000],
        allowed_percentages=[15.0],
    )
    assert ok is True
    assert not errors


def test_validation_fails_fabricated_number():
    text = "Net interest income increased from $10.0B to $12.5B."
    ok, errors = validate_explanation_numbers(
        text,
        allowed_values=[10_000_000_000, 11_500_000_000],
        allowed_percentages=[15.0],
    )
    assert ok is False
    assert errors


def test_validation_fails_wrong_percentage():
    text = "Revenue increased by 25% from $100M to $120M."
    ok, errors = validate_explanation_numbers(
        text,
        allowed_values=[100_000_000, 120_000_000],
        allowed_percentages=[20.0],
    )
    assert ok is False
