from app.db.models import Approval, Bank, Explanation, FinancialStatement, FluxAnalysis


def test_models_registered():
    assert Bank.__tablename__ == "banks"
    assert FinancialStatement.__tablename__ == "financial_statements"
    assert FluxAnalysis.__tablename__ == "flux_analyses"
    assert Explanation.__tablename__ == "explanations"
    assert Approval.__tablename__ == "approvals"
