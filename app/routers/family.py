from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

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
def get_user_totals(db: Session, user_id):
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


# --------- GET /family  → list các member mà user đang xem ---------
@router.get("/", response_model=list[FamilyMemberOut])
def list_family(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # lấy record liên kết mà mình là owner
    links = (
        db.query(FamilyMember, User)
        .join(User, FamilyMember.member_id == User.id)
        .filter(FamilyMember.owner_id == user.id)
        .all()
    )

    result: list[FamilyMemberOut] = []

    for link, member in links:
        total_income, total_expense = get_user_totals(db, member.id)
        result.append(
            FamilyMemberOut(
                id=link.id,
                member_id=member.id,
                email=member.email,
                total_income=total_income,
                total_expense=total_expense,
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
    # không cho add chính mình
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

    # check đã tồn tại link chưa
    exists = (
        db.query(FamilyMember)
        .filter(
            FamilyMember.owner_id == user.id,
            FamilyMember.member_id == member.id,
        )
        .first()
    )
    if exists:
        # trả về luôn, k tạo thêm
        total_income, total_expense = get_user_totals(db, member.id)
        return FamilyMemberOut(
            id=exists.id,
            member_id=member.id,
            email=member.email,
            total_income=total_income,
            total_expense=total_expense,
        )

    # tạo link mới
    link = FamilyMember(owner_id=user.id, member_id=member.id)
    db.add(link)
    db.commit()
    db.refresh(link)

    total_income, total_expense = get_user_totals(db, member.id)
 total_wallet = (
        db.query(func.coalesce(func.sum(Wallet.balance), 0.0))
        .filter(Wallet.user_id == link.member_id)
        .scalar()
        or 0.0
    )
    return FamilyMemberOut(
        id=link.id,
        member_id=member.id,
        email=member.email,
        total_income=total_income,
        total_expense=total_expense,
        total_wallet_balance=total_wallet_balance,
    )


# --------- GET /family/{member_id}/transactions ---------
@router.get("/{member_id}/transactions", response_model=list[TransactionOut])
def member_transactions(
    member_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # chỉ cho xem nếu có link owner->member
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
