from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("/", response_model=list[TransactionOut])
def list_transactions(db: Session = Depends(get_db), user = Depends(get_current_user)):
    return db.query(Transaction).filter(Transaction.user_id == user.id).order_by(Transaction.date.desc()).all()

@router.post("/", response_model=TransactionOut)
def create_tx(data: TransactionCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    new = Transaction(user_id=user.id, **data.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

@router.delete("/{tx_id}")
def delete_tx(tx_id: str, db: Session = Depends(get_db), user = Depends(get_current_user)):
    db.query(Transaction).filter(Transaction.id == tx_id, Transaction.user_id == user.id).delete()
    db.commit()
    return {"deleted": True}
