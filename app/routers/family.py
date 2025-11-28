from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.services.auth import get_current_user
from app.models.user import User          # chỉnh lại nếu file khác tên
from app.models.transaction import Transaction
from app.models.family_link import FamilyLink
from app.schemas.family import FamilyMemberOut, FamilyAddRequest

router = APIRouter(prefix="/family", tags=["Family"])


@router.post("/", response_model=FamilyMemberOut)
def add_family_member(
    payload: FamilyAddRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # không cho add chính mình
    member = db.query(User).filter(User.email == payload.email).first()
    if not member:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản với email này")

    if member.id == user.id:
        raise HTTPException(status_code=400, detail="Không thể thêm chính bạn vào gia đình")

    # check trùng
    existing = (
        db.query(FamilyLink)
        .filter(FamilyLink.owner_id == user.id, FamilyLink.member_id == member.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Tài khoản này đã nằm trong danh sách gia đình")

    link = FamilyLink(owner_id=user.id, member_id=member.id)
    db.add(link)
    db.commit()

    # tổng thu / chi
    income_sum, expense_sum = (
        db.query(
            func.coalesce(
                func.sum(func.case((Transaction.type == "income", Transaction.amount))), 0
            ),
            func.coalesce(
                func.sum(func.case((Transaction.type == "expense", Transaction.amount))), 0
            ),
        )
        .filter(Transaction.user_id == member.id)
        .first()
    )

    return FamilyMemberOut(
        member_id=member.id,
        email=member.email,
        total_income=float(income_sum or 0),
        total_expense=float(expense_sum or 0),
    )


@router.get("/", response_model=list[FamilyMemberOut])
def list_family_members(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # lấy list member_id
    links = (
        db.query(FamilyLink)
        .filter(FamilyLink.owner_id == user.id)
        .all()
    )
    if not links:
        return []

    member_ids = [l.member_id for l in links]

    # lấy info user
    users = db.query(User).filter(User.id.in_(member_ids)).all()
    users_by_id = {u.id: u for u in users}

    # tổng thu / chi cho từng member
    agg = (
        db.query(
            Transaction.user_id,
            func.coalesce(
                func.sum(
                    func.case(
                        (Transaction.type == "income", Transaction.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("income"),
            func.coalesce(
                func.sum(
                    func.case(
                        (Transaction.type == "expense", Transaction.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("expense"),
        )
        .filter(Transaction.user_id.in_(member_ids))
        .group_by(Transaction.user_id)
        .all()
    )
    sums_by_user = {row.user_id: row for row in agg}

    out = []
    for mid in member_ids:
      u = users_by_id.get(mid)
      if not u:
          continue
      sums = sums_by_user.get(mid)
      income = float(getattr(sums, "income", 0) or 0)
      expense = float(getattr(sums, "expense", 0) or 0)
      out.append(
          FamilyMemberOut(
              member_id=mid,
              email=u.email,
              total_income=income,
              total_expense=expense,
          )
      )
    return out


@router.get("/{member_id}/transactions")
def list_member_transactions(
    member_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Lấy lịch sử thu chi của 1 tài khoản trong gia đình
    """
    # verify người này thực sự nằm trong family của user
    link = (
        db.query(FamilyLink)
        .filter(FamilyLink.owner_id == user.id, FamilyLink.member_id == member_id)
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

    # trả raw, app đã có logic map category ở AppContext nếu cần
    return txs
