# app/routers/family.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.database import get_db
from app.notifications import send_notification_to_token
from firebase_admin import messaging
from app.models.user import User
from app.models.transaction import Transaction
from app.models.wallet import Wallet
from app.models.family_member import FamilyMember
from app.schemas.family_member import (
    FamilyAddRequest,
    FamilyMemberOut,
    FamilyInvitationOut,
    FamilyJoinedOut,
)
from app.schemas.transaction import TransactionOut
from app.services.auth import get_current_user

router = APIRouter(prefix="/family", tags=["Family"])


# --------- helper: tính tổng thu / chi của 1 user ---------
def get_user_totals(db: Session, user_id: UUID):
    q = (
        db.query(
            Transaction.type,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .filter(Transaction.user_id == user_id)
        .group_by(Transaction.type)
    )

    total_income = 0.0
    total_expense = 0.0

    for row in q:
        if row.type == "income":
            total_income = float(row.total or 0)
        elif row.type == "expense":
            total_expense = float(row.total or 0)

    return total_income, total_expense


# --------- helper: tính số dư hiện tại của ví user ---------
def get_user_current_wallet_balance(
    db: Session,
    user_id: UUID,
    total_income: float,
    total_expense: float,
) -> float:
    initial_balance = (
        db.query(func.coalesce(func.sum(Wallet.balance), 0.0))
        .filter(Wallet.user_id == user_id)
        .scalar()
        or 0.0
    )
    current_wallet_balance = initial_balance + total_income - total_expense
    return float(current_wallet_balance)


# --------- GET /family ---------
@router.get("/", response_model=list[FamilyMemberOut])
def list_family(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    links = (
        db.query(FamilyMember, User)
        .join(User, FamilyMember.member_id == User.id)
        .filter(FamilyMember.owner_id == user.id)
        .all()
    )

    result: list[FamilyMemberOut] = []

    for link, member in links:
        total_income = 0.0
        total_expense = 0.0
        total_wallet_balance = 0.0

        if link.status == "accepted":
            total_income, total_expense = get_user_totals(db, member.id)
            total_wallet_balance = get_user_current_wallet_balance(
                db, member.id, total_income, total_expense
            )

        display_name = (
            getattr(link, "display_name", None)
            or getattr(member, "full_name", None)
            or getattr(member, "name", None)
            or member.email.split("@")[0]
        )

        result.append(
            FamilyMemberOut(
                id=link.id,
                member_id=member.id,
                email=member.email,
                display_name=display_name,
                total_income=total_income,
                total_expense=total_expense,
                total_wallet_balance=total_wallet_balance,
                status=link.status,
                group_name=getattr(link, "group_name", None)
            )
        )

    return result


# --------- POST /family → gửi lời mời (theo nhóm) ---------
@router.post("/", response_model=FamilyMemberOut)
def add_family_member(
    payload: FamilyAddRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # không cho tự add chính mình
    if payload.email.lower() == user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể thêm chính tài khoản của bạn",
        )

    # tìm user theo email
    member = db.query(User).filter(User.email == payload.email).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài khoản với email này",
        )

    # tên nhóm: nếu không gửi thì mặc định "Gia đình"
    group_name = (payload.group_name or "Gia đình").strip()

    display_name = (
        payload.display_name
        or getattr(member, "full_name", None)
        or getattr(member, "name", None)
        or member.email.split("@")[0]
    )

    # ⚠️ check trùng link THEO NHÓM
    link = (
        db.query(FamilyMember)
        .filter(
            FamilyMember.owner_id == user.id,
            FamilyMember.member_id == member.id,
            FamilyMember.group_name == group_name,   # 👈 thêm
        )
        .first()
    )

    if link:
        total_income = 0.0
        total_expense = 0.0
        total_wallet_balance = 0.0

        if link.status == "accepted":
            total_income, total_expense = get_user_totals(db, member.id)
            total_wallet_balance = get_user_current_wallet_balance(
                db, member.id, total_income, total_expense
            )

        return FamilyMemberOut(
            id=link.id,
            member_id=member.id,
            email=member.email,
            display_name=display_name,
            total_income=total_income,
            total_expense=total_expense,
            total_wallet_balance=total_wallet_balance,
            status=link.status,
            group_name=link.group_name,   # 👈 nhớ trả luôn
        )

    # tạo link mới
    link = FamilyMember(
        owner_id=user.id,
        member_id=member.id,
        status="pending",
        group_name=group_name,  # 👈 gắn nhóm
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    # gửi thông báo nếu có token
    if getattr(member, "fcm_token", None):
        owner_name = user.email.split("@")[0]
        send_notification_to_token(
            member.fcm_token,
            title="Lời mời tham gia nhóm",
            body=f"{owner_name} vừa mời bạn vào nhóm chi tiêu '{group_name}'",
            data={"type": "family_invite"},
        )

    print("👉 member email:", member.email, "fcm_token:", member.fcm_token)

    return FamilyMemberOut(
        id=link.id,
        member_id=member.id,
        email=member.email,
        display_name=display_name,
        total_income=0.0,
        total_expense=0.0,
        total_wallet_balance=0.0,
        status=link.status,
        group_name=link.group_name,
    )


# --------- GET /family/invitations ---------
@router.get("/invitations", response_model=list[FamilyInvitationOut])
def my_invitations(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    links = (
        db.query(FamilyMember, User)
        .join(User, FamilyMember.owner_id == User.id)
        .filter(
            FamilyMember.member_id == user.id,
            FamilyMember.status == "pending",
        )
        .all()
    )

    result: list[FamilyInvitationOut] = []

    for link, owner in links:
        owner_display_name = (
            getattr(owner, "full_name", None)
            or getattr(owner, "name", None)
            or owner.email.split("@")[0]
        )
        result.append(
            FamilyInvitationOut(
                id=link.id,
                owner_id=owner.id,
                owner_email=owner.email,
                owner_display_name=owner_display_name,
                status=link.status,
                created_at=link.created_at,
            )
        )

    return result


# --------- POST /family/{link_id}/accept ---------
@router.post("/{link_id}/accept")
def accept_family_invitation(
    link_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    link = db.query(FamilyMember).filter(FamilyMember.id == link_id).first()
    if not link or link.member_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lời mời không tồn tại",
        )

    link.status = "accepted"
    db.commit()
    db.refresh(link)

    owner = db.query(User).filter(User.id == link.owner_id).first()

    if owner and owner.fcm_token:
        member_name = user.email.split("@")[0]
        send_notification_to_token(
            owner.fcm_token,
            title="Lời mời đã được chấp nhận",
            body=f"{member_name} đã đồng ý tham gia nhóm của bạn",
            data={"type": "family_invite_accepted"},
        )

    return {"status": "accepted"}


# --------- POST /family/{link_id}/reject ---------
@router.post("/{link_id}/reject")
def reject_family_invitation(
    link_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    link = db.query(FamilyMember).filter(FamilyMember.id == link_id).first()
    if not link or link.member_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lời mời không tồn tại",
        )

    link.status = "rejected"
    db.commit()
    return {"status": "rejected"}


# --------- GET /family/{member_id}/transactions ---------
@router.get("/{member_id}/transactions", response_model=list[TransactionOut])
def member_transactions(
    member_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    link = (
        db.query(FamilyMember)
        .filter(
            FamilyMember.owner_id == user.id,
            FamilyMember.member_id == member_id,
        )
        .first()
    )

    if not link or link.status != "accepted":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản này chưa xác nhận tham gia gia đình",
        )

    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == member_id)
        .order_by(Transaction.date.desc())
        .all()
    )

    return txs


# --------- DELETE /family/{member_id} ---------
@router.delete("/{member_id}")
def remove_family_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    link = (
        db.query(FamilyMember)
        .filter(
            FamilyMember.owner_id == user.id,
            FamilyMember.member_id == member_id,
        )
        .first()
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thành viên không tồn tại trong gia đình",
        )

    db.delete(link)
    db.commit()
    return {"deleted": True}

@router.get("/joined", response_model=list[FamilyJoinedOut])
def my_joined_groups(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    links = (
        db.query(FamilyMember, User)
        .join(User, FamilyMember.owner_id == User.id)
        .filter(
            FamilyMember.member_id == user.id,
            FamilyMember.status == "accepted",
        )
        .order_by(FamilyMember.created_at.asc())
        .all()
    )

    result: list[FamilyJoinedOut] = []

    for link, owner in links:
        owner_display_name = (
            getattr(owner, "full_name", None)
            or getattr(owner, "name", None)
            or owner.email.split("@")[0]
        )

        result.append(
            FamilyJoinedOut(
                id=link.id,
                owner_id=owner.id,
                owner_email=owner.email,
                owner_display_name=owner_display_name,
                group_name=link.group_name,
                status=link.status,
                created_at=link.created_at,
            )
        )

    return result

@router.post("/{link_id}/leave")
def leave_family_group(
    link_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    link = (
        db.query(FamilyMember)
        .filter(
            FamilyMember.id == link_id,
            FamilyMember.member_id == user.id,
            FamilyMember.status == "accepted",
        )
        .first()
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bạn không còn ở nhóm này hoặc nhóm không tồn tại",
        )

    db.delete(link)
    db.commit()
    return {"left": True}    