from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.models.user import User
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == data.email).first()
    if exists:
        raise HTTPException(400, "Email đã tồn tại")

    user = User(email=data.email, password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(400, "Sai email hoặc mật khẩu")

    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": str(user.id), "email": user.email}
    }
