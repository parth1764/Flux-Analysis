from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "flux-analysis-automator"


def test_openapi_available():
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "Flux Analysis Automator" in response.json()["info"]["title"]


def test_banks_endpoint(client):
    response = client.get("/api/banks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_approval_rejects_failed_validation(client, db_session):
    from app.db.models import (
        ApprovalStatus,
        Bank,
        Explanation,
        FluxAnalysis,
        MaterialityStatus,
        ValidationStatus,
    )
    from app.db.repositories.financial_repos import ApprovalRepository

    bank = Bank(name="Test", ticker="TST", country="US", currency="USD")
    db_session.add(bank)
    db_session.commit()
    flux = FluxAnalysis(
        bank_id=bank.id,
        current_period="2025-Q2",
        previous_period="2025-Q1",
        metric_name="Net Income",
        previous_value=100,
        current_value=120,
        absolute_change=20,
        percentage_change=20,
        percentage_change_defined=True,
        materiality_status=MaterialityStatus.MATERIAL,
    )
    db_session.add(flux)
    db_session.commit()
    expl = Explanation(
        flux_id=flux.id,
        generated_explanation="Net income changed.",
        validation_status=ValidationStatus.FAILED,
    )
    db_session.add(expl)
    db_session.commit()
    ApprovalRepository(db_session).ensure_pending_for_flux(flux.id)

    response = client.post(
        f"/api/explanations/{expl.id}/approve",
        json={"reviewer": "cfo@bank.com", "comment": "approve"},
    )
    assert response.status_code == 400
