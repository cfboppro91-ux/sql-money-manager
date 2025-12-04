# app/routers/transaction.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.models.family_member import FamilyMember
from app.schemas.transaction import TransactionCreate, TransactionOut
from app.services.auth import get_current_user
from app.notifications import send_notification_to_token  # 👈 dùng FCM

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# --------- helper: notify owner khi mình có giao dịch mới ---------
def notify_family_new_transaction(
    db: Session,
    member_user: User,       # người đang tạo giao dịch (current user)
    tx: Transaction,
):
    """
    Gửi FCM cho tất cả owner đã link với user này (status = accepted)
    khi user thêm 1 giao dịch mới.
    """
    # tìm tất cả owner đã liên kết mình (mình là member_id)
    links = (
        db.query(FamilyMember, User)
        .join(User, FamilyMember.owner_id == User.id)
        .filter(
            FamilyMember.member_id == member_user.id,
            FamilyMember.status == "accepted",
        )
        .all()
    )

    if not links:
        return

    tx_type_vi = "khoản thu" if tx.type == "income" else "khoản chi"
    amount = int(tx.amount or 0)

    member_name = (
        getattr(member_user, "full_name", None)
        or getattr(member_user, "name", None)
        or member_user.email.split("@")[0]
    )

    for link, owner in links:
        # owner là user "chủ nhóm"
        token = getattr(owner, "fcm_token", None)
        if not token:
          continue

        body = f"{member_name} vừa thêm {tx_type_vi} {amount:,.0f}đ"

        send_notification_to_token(
            token,
            title="Giao dịch mới trong nhóm",
            body=body,
            data={
                "type": "family_tx",
                "member_id": str(member_user.id),
                "tx_id": str(tx.id),
                "tx_type": tx.type,
            },
        )


# --------- list giao dịch của chính mình ---------
@router.get("/", response_model=list[TransactionOut])
def list_transactions(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user.id)
        .order_by(Transaction.date.desc())
        .all()
    )


# --------- tạo giao dịch ---------
@router.post("/", response_model=TransactionOut)
def create_tx(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    new = Transaction(user_id=user.id, **data.dict())
    db.add(new)
    db.commit()
    db.refresh(new)

    # ⭐ gọi notify sau khi create
    notify_family_new_transaction(db, user, new)

    return new


# --------- xoá giao dịch ---------
@router.delete("/{tx_id}")
def delete_tx(
    tx_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db.query(Transaction).filter(
        Transaction.id == tx_id,
        Transaction.user_id == user.id,
    ).delete()
    db.commit()
    return {"deleted": True}

@router.put("/{tx_id}", response_model=TransactionOut)
def update_tx(data: TransactionCreate, tx_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.user_id == user.id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Not found")
    # update fields
    tx.type = data.type
    tx.amount = data.amount
    tx.note = data.note
    tx.category_id = data.category_id
    if hasattr(data, "date") and data.date:
        tx.date = data.date
    tx.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(tx)
    return tx