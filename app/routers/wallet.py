# router/wallet.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate, WalletOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/wallets", tags=["Wallets"])

@router.get("/", response_model=list[WalletOut])
def list_wallets(db: Session = Depends(get_db), user = Depends(get_current_user)):
    return db.query(Wallet).filter(Wallet.user_id == user.id).all()

@router.post("/", response_model=WalletOut, status_code=status.HTTP_201_CREATED)
def create_wallet(data: WalletCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    new = Wallet(user_id=user.id, **data.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

@router.put("/{wallet_id}", response_model=WalletOut)
def update_wallet(wallet_id: str, data: WalletCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    # tìm wallet
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id, Wallet.user_id == user.id).first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")

    # cập nhật các field (an toàn)
    for k, v in data.dict().items():
        setattr(wallet, k, v)

    db.add(wallet)
    db.commit()
    db.refresh(wallet)

    return wallet
