from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.budget import Budget
from app.schemas.budget import BudgetCreate, BudgetOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/budgets", tags=["Budgets"])

@router.get("/", response_model=list[BudgetOut])
def list_budgets(db: Session = Depends(get_db), user = Depends(get_current_user)):
    return db.query(Budget).filter(Budget.user_id == user.id).all()

@router.post("/", response_model=BudgetOut)
def create_budget(data: BudgetCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    new = Budget(user_id=user.id, **data.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

@router.delete("/{budget_id}")
def delete_budget(budget_id: str, db: Session = Depends(get_db), user = Depends(get_current_user)):
    db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user.id).delete()
    db.commit()
    return {"deleted": True}
