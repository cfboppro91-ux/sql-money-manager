# app/routers/family.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.models.wallet import Wallet
from app.models.family_member import FamilyMember
from app.schemas.family_member import FamilyAddRequest, FamilyMemberOut
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


# --------- helper: tính SỐ DƯ HIỆN TẠI của ví 1 user ---------
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


# --------- GET /family  → list các member mà user đang xem ---------
@router.get("/", response_model=list[FamilyMemberOut])
def list_family(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    links = (
        db.query(FamilyMember, User)
        .join(User, FamilyMember.member_id == User.id)
        .filter(
            FamilyMember.owner_id == user.id,
            FamilyMember.status == "accepted",   # ✅ chỉ lấy accepted
        )
        .all()
    )

    result: list[FamilyMemberOut] = []

    for link, member in links:
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
            )
        )

    return result
    


# --------- POST /family  → thêm 1 tài khoản khác bằng email ---------
@router.post("/", response_model=FamilyMemberOut)
def add_family_member(
    payload: FamilyAddRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if payload.email.lower() == user.email.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể thêm chính tài khoản của bạn",
        )

    member = db.query(User).filter(User.email == payload.email).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy tài khoản với email này",
        )

    display_name = (
        payload.display_name
        or getattr(member, "full_name", None)
        or getattr(member, "name", None)
        or member.email.split("@")[0]
    )

    # check đã tồn tại link chưa
    link = (
        db.query(FamilyMember)
        .filter(
            FamilyMember.owner_id == user.id,
            FamilyMember.member_id == member.id,
        )
        .first()
    )
    if link:
        # nếu đã từng tồn tại, giữ nguyên status (pending/accepted/...)
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
        )

    # ✅ tạo link mới với status = pending
    link = FamilyMember(
        owner_id=user.id,
        member_id=member.id,
        status="pending",
    )
    db.add(link)
    db.commit()
    db.refresh(link)

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
        status=link.status,  # -> "pending"
    )

    # tạo link mới (nếu chưa có cột display_name thì tạm thời chỉ lưu owner_id + member_id)
    link = FamilyMember(owner_id=user.id, member_id=member.id)
    db.add(link)
    db.commit()
    db.refresh(link)

    total_income, total_expense = get_user_totals(db, member.id)
    total_wallet_balance = get_user_current_wallet_balance(
        db, member.id, total_income, total_expense
    )

    return FamilyMemberOut(
        id=link.id,
        member_id=member.id,
        email=member.email,
        display_name=display_name,  # ✅ TRẢ VỀ TÊN
        total_income=total_income,
        total_expense=total_expense,
        total_wallet_balance=total_wallet_balance,
    )
    # --------- GET /family/invitations  → user xem các lời mời mình được add ---------
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


# --------- POST /family/{link_id}/accept  → member chấp nhận ---------
@router.post("/{link_id}/accept")
def accept_family_invitation(
    link_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    link = (
        db.query(FamilyMember)
        .filter(FamilyMember.id == link_id)
        .first()
    )
    if not link or link.member_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lời mời không tồn tại",
        )

    link.status = "accepted"
    db.commit()
    db.refresh(link)
    return {"status": "accepted"}


# --------- POST /family/{link_id}/reject  → member từ chối ---------
@router.post("/{link_id}/reject")
def reject_family_invitation(
    link_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    link = (
        db.query(FamilyMember)
        .filter(FamilyMember.id == link_id)
        .first()
    )
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
    if not link or link.status != "accepted":  # ✅ phải accepted
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
    if not link:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem tài khoản này",
        )

    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == member_id)
        .order_by(Transaction.date.desc())
        .all()
    )
    return txs


# --------- DELETE /family/{member_id} → xoá khỏi gia đình ---------
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
