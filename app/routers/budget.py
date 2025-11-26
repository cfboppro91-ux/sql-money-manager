from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetOut, BudgetUpdate
from app.services.auth import get_current_user

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("/", response_model=list[BudgetOut])
def list_budgets(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return db.query(Budget).filter(Budget.user_id == user.id).all()


@router.post("/", response_model=BudgetOut)
def create_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    new = Budget(user_id=user.id, **data.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@router.put("/{budget_id}", response_model=BudgetOut)
def update_budget(
    budget_id: UUID,
    data: BudgetUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    q = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user.id,
    )
    budget = q.first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(budget, key, value)

    db.commit()
    db.refresh(budget)
    return budget


@router.delete("/{budget_id}")
def delete_budget(
    budget_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == user.id,
    ).delete()
    db.commit()
    return {"deleted": True}
