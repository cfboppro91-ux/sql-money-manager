from fastapi import HTTPException, Depends, Header, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.user import User


def get_current_user(
    authorization: str = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu token trong header Authorization",
        )

    # "Bearer <token>" -> "<token>"
    token = authorization.replace("Bearer ", "").strip()

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không hợp lệ (không có user id)",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User không tồn tại",
        )

    return user