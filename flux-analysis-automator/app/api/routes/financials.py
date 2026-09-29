from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories.financial_repos import BankRepository, FinancialRepository
from app.schemas.common import FinancialOut

router = APIRouter(prefix="/financials", tags=["financials"])


@router.get("", response_model=list[FinancialOut])
def list_financials(
    bank_id: int | None = None,
    limit: int = Query(200, le=2000),
    db: Session = Depends(get_db),
):
    return FinancialRepository(db).list_financials(bank_id=bank_id, limit=limit)


@router.get("/{bank_id}", response_model=list[FinancialOut])
def financials_by_bank(bank_id: int, db: Session = Depends(get_db)):
    if not BankRepository(db).get_by_id(bank_id):
        raise HTTPException(status_code=404, detail="Bank not found")
    return FinancialRepository(db).list_financials(bank_id=bank_id, limit=2000)
