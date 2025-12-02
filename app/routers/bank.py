# app/routers/bank.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.services.auth import get_current_user
from app.models.bank_account import BankAccount
from app.models.bank_transaction import BankTransaction
from app.models.family_member import FamilyMember
from app.models.user import User
from app.notifications import send_notification_to_token
from app.schemas.bank import (
    BankAccountCreate,
    BankAccountOut,
    BankTransactionCreate,
    BankTransactionOut,
)

router = APIRouter(prefix="/bank", tags=["Bank"])


# --------- GET /bank/accounts  → list account ngân hàng của user ---------
@router.get("/accounts", response_model=list[BankAccountOut])
def list_bank_accounts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    accounts = (
        db.query(BankAccount)
        .filter(BankAccount.user_id == user.id)
        .order_by(BankAccount.created_at.asc())
        .all()
    )
    return accounts


# --------- POST /bank/accounts  → tạo 1 account ngân hàng ---------
@router.post("/accounts", response_model=BankAccountOut, status_code=status.HTTP_201_CREATED)
def create_bank_account(
    payload: BankAccountCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    acc = BankAccount(
        user_id=user.id,
        bank_name=payload.bank_name,
        account_number=payload.account_number,
        balance=payload.balance,
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


# --------- GET /bank/accounts/{account_id}/transactions  → history ---------
@router.get(
    "/accounts/{account_id}/transactions",
    response_model=list[BankTransactionOut],
)
def list_bank_transactions(
    account_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # check quyền sở hữu acc
    acc = (
        db.query(BankAccount)
        .filter(
            BankAccount.id == account_id,
            BankAccount.user_id == user.id,
        )
        .first()
    )
    if not acc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài khoản ngân hàng không tồn tại",
        )

    txs = (
        db.query(BankTransaction)
        .filter(BankTransaction.account_id == account_id)
        .order_by(BankTransaction.date.desc())
        .all()
    )
    return txs


# --------- POST /bank/accounts/{account_id}/transactions  → tạo giao dịch ---------
@router.post(
    "/accounts/{account_id}/transactions",
    response_model=BankTransactionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_bank_transaction(
    account_id: UUID,
    payload: BankTransactionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    acc = (
        db.query(BankAccount)
        .filter(
            BankAccount.id == account_id,
            BankAccount.user_id == user.id,
        )
        .first()
    )
    if not acc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tài khoản ngân hàng không tồn tại",
        )

    # validate type
    if payload.type not in ("income", "expense"):
        raise HTTPException(400, "type phải là 'income' hoặc 'expense'")

    # cập nhật số dư
    if payload.type == "income":
        acc.balance = (acc.balance or 0) + payload.amount
    else:
        acc.balance = (acc.balance or 0) - payload.amount

    tx = BankTransaction(
        account_id=account_id,
        type=payload.type,
        amount=payload.amount,
        description=payload.description,
        date=payload.date or datetime.utcnow(),
        balance_after=acc.balance,
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)
    db.refresh(acc)

    # 🔔 GỬI FCM CHO CÁC OWNER ĐANG THEO DÕI USER NÀY
    # user hiện tại = member, tìm các owner có gia đình với user này
    links = (
        db.query(FamilyMember, User)
        .join(User, FamilyMember.owner_id == User.id)
        .filter(
            FamilyMember.member_id == user.id,
            FamilyMember.status == "accepted",
        )
        .all()
    )

    member_name = user.email.split("@")[0]
    action_word = "nhận" if tx.type == "income" else "chi"
    amount_str = f"{int(tx.amount):,}đ".replace(",", ".")

    for link, owner in links:
        if getattr(owner, "fcm_token", None):
            send_notification_to_token(
                owner.fcm_token,
                title="Giao dịch ngân hàng mới",
                body=f"{member_name} vừa {action_word} {amount_str} qua ngân hàng",
                data={
                    "type": "bank_tx_changed",
                    "member_id": str(user.id),
                    "account_id": str(acc.id),
                    "tx_id": str(tx.id),
                },
            )

    return tx