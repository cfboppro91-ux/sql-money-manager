# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import secrets

from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserOut, FCMTokenIn, ForgotPasswordIn
from app.models.user import User
from app.security import hash_password, verify_password, create_access_token
from app.services.auth import get_current_user  # 👈 dùng để lấy user từ JWT
from app.services.email import send_email

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

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordIn, db: Session = Depends(get_db)):
    # 1. Tìm user theo email
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        # không nên leak quá nhiều info, nhưng cho app học tập thì báo thẳng cũng được
        raise HTTPException(status_code=404, detail="Email không tồn tại")

    # 2. Tạo mật khẩu mới random
    new_password = secrets.token_urlsafe(8)  # vd: 'aB3_xYz12'

    # 3. Hash & lưu DB
    user.password = hash_password(new_password)
    db.commit()
    db.refresh(user)

    # 4. Soạn nội dung email
    subject = "Đặt lại mật khẩu - Money Manager"
    body = f"""
Xin chào {user.email},

Mật khẩu mới cho tài khoản Money Manager của bạn là:

    {new_password}

Vui lòng đăng nhập và đổi lại mật khẩu trong phần cài đặt để đảm bảo an toàn.

Nếu bạn không yêu cầu đặt lại mật khẩu, hãy bỏ qua email này.

Trân trọng,
Money Manager
"""

    ok = send_email(user.email, subject, body)
    if not ok:
        # DEV: tạm return 500 + message dễ hiểu hơn
        raise HTTPException(
            status_code=500,
            detail="DEV: send_email() trả về False. Vào Render Logs xem 'Error sending email' để biết lý do.",
        )

    return {"detail": "Mật khẩu mới đã được gửi qua email của bạn."}