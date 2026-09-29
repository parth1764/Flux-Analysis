from app.utils.financial_utils import calculate_flux


def test_flux_positive_change():
    result = calculate_flux(100, 120)
    assert result.absolute_change == 20
    assert result.percentage_change == 20.0
    assert result.percentage_change_defined is True


def test_flux_negative_change():
    result = calculate_flux(100, 80)
    assert result.absolute_change == -20
    assert result.percentage_change == -20.0


def test_flux_zero_previous():
    result = calculate_flux(0, 100)
    assert result.absolute_change == 100
    assert result.percentage_change is None
    assert result.percentage_change_defined is False
