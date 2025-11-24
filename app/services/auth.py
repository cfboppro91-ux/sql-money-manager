from fastapi import HTTPException, Depends
from jose import jwt
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User

def get_current_user(db: Session = Depends(get_db), token: str = Depends(lambda: None)):
    from fastapi import Header
    token = Header(default=None, alias="Authorization")

    if token is None:
        raise HTTPException(401, "Thiếu token")

    token = token.replace("Bearer ", "")

    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = data["sub"]
    except:
        raise HTTPException(401, "Token không hợp lệ")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User không tồn tại")

    return user
