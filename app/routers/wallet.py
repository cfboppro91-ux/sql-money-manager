from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate, WalletOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/wallets", tags=["Wallets"])

@router.get("/", response_model=list[WalletOut])
def list_wallets(db: Session = Depends(get_db), user = Depends(get_current_user)):
    return db.query(Wallet).filter(Wallet.user_id == user.id).all()

@router.post("/", response_model=WalletOut)
def create_wallet(data: WalletCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    new = Wallet(user_id=user.id, **data.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

@router.put("/{wallet_id}")
def update_wallet(wallet_id: str, data: WalletCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    db.query(Wallet).filter(Wallet.id == wallet_id, Wallet.user_id == user.id).update(data.dict())
    db.commit()
    return {"updated": True}
