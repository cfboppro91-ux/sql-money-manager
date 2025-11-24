from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryOut
from app.models.category import Category
from app.services.auth import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db), user = Depends(get_current_user)):
    return db.query(Category).filter(Category.user_id == user.id).all()

@router.post("/", response_model=CategoryOut)
def create_category(data: CategoryCreate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    new = Category(user_id=user.id, **data.dict())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

@router.delete("/{cat_id}")
def delete_category(cat_id: str, db: Session = Depends(get_db), user = Depends(get_current_user)):
    db.query(Category).filter(
        Category.id == cat_id,
        Category.user_id == user.id
    ).delete()
    db.commit()
    return {"deleted": True}
