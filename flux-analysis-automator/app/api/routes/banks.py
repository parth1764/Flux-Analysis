from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repositories.financial_repos import BankRepository
from app.schemas.common import BankOut

router = APIRouter(prefix="/banks", tags=["banks"])


@router.get("", response_model=list[BankOut])
def list_banks(db: Session = Depends(get_db)):
    return BankRepository(db).list_banks()
