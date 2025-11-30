# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserOut, FCMTokenIn
from app.models.user import User
from app.security import hash_password, verify_password, create_access_token
from app.services.auth import get_current_user  # 👈 dùng để lấy user từ JWT

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
        "user": {"id": str(user.id), "email": user.email},
    }


# 👇 ENDPOINT CẬP NHẬT FCM TOKEN
@router.post("/set-fcm-token")
def set_fcm_token(
    payload: FCMTokenIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.fcm_token:
        raise HTTPException(400, "Thiếu fcm_token")

    current_user.fcm_token = payload.fcm_token
    db.commit()
    db.refresh(current_user)

    print("✅ Updated FCM token for:", current_user.email)

    return {"ok": True}
