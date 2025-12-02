# app/routers/bank.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.bank_account import BankAccount
from app.models.bank_transaction import BankTransaction
from app.schemas.bank import BankAccountOut, BankTransactionOut, SimulateTxIn
from app.services.auth import get_current_user

router = APIRouter(prefix="/bank", tags=["Bank"])


@router.get("/accounts", response_model=list[BankAccountOut])
def list_bank_accounts(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    accounts = db.query(BankAccount).filter(BankAccount.user_id == user.id).all()
    return accounts


@router.get("/accounts/{account_id}/transactions", response_model=list[BankTransactionOut])
def list_bank_transactions(
    account_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    account = (
        db.query(BankAccount)
        .filter(BankAccount.id == account_id, BankAccount.user_id == user.id)
        .first()
    )
    if not account:
        raise HTTPException(404, "Không tìm thấy tài khoản ngân hàng")

    txs = (
        db.query(BankTransaction)
        .filter(BankTransaction.account_id == account_id)
        .order_by(BankTransaction.date.desc())
        .all()
    )
    return txs


# fake ngân hàng: tạo giao dịch & cập nhật balance
@router.post("/accounts/{account_id}/simulate-tx", response_model=BankTransactionOut)
def simulate_bank_tx(
    account_id: UUID,
    payload: SimulateTxIn,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    account = (
        db.query(BankAccount)
        .filter(BankAccount.id == account_id, BankAccount.user_id == user.id)
        .first()
    )
    if not account:
        raise HTTPException(404, "Không tìm thấy tài khoản ngân hàng")

    if payload.type not in ("income", "expense"):
        raise HTTPException(400, "type phải là income hoặc expense")

    amount = float(payload.amount or 0)
    if amount <= 0:
        raise HTTPException(400, "amount phải > 0")

    # update số dư
    if payload.type == "income":
      account.balance += amount
    else:
      account.balance -= amount

    tx = BankTransaction(
        account_id=account.id,
        type=payload.type,
        amount=amount,
        description=payload.description,
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)
    db.refresh(account)

    # OPTIONAL: gửi FCM notif cho owner (giống flow family)
    # => có thể dùng send_notification_to_token + user.fcm_token
    # title = "Giao dịch ngân hàng mới"
    # body = f"{payload.type == 'income' and '+' or '-'}{int(amount)} vào {account.bank_name}"
    # send_notification_to_token(...)

    return tx
