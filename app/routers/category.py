# app/routers/category.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryOut
from app.models.category import Category
from app.services.auth import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    cats = (
        db.query(Category)
        .filter(Category.user_id == user.id)
        .order_by(Category.created_at.desc())
        .all()
    )

    # Trả list dict cho chắc
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "icon": c.icon,
            "color": c.color,
        }
        for c in cats
    ]


@router.post("/", response_model=CategoryOut, status_code=201)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    new = Category(
        user_id=user.id,
        **data.model_dump(),   # nếu đang dùng pydantic v2
        # **data.dict(),       # nếu bro vẫn xài pydantic v1
    )
    db.add(new)
    db.commit()
    db.refresh(new)

    # Trả dict thuần, tránh lỗi Pydantic-ORM
    return {
        "id": str(new.id),
        "name": new.name,
        "icon": new.icon,
        "color": new.color,
    }


@router.delete("/{cat_id}")
def delete_category(
    cat_id: str,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    (
        db.query(Category)
        .filter(
            Category.id == cat_id,
            Category.user_id == user.id,
        )
        .delete()
    )
    db.commit()
    return {"deleted": True}
