# schema/wallet.py
from pydantic import BaseModel
from uuid import UUID  # 👈 thêm cái này

class WalletBase(BaseModel):
    balance: float

class WalletCreate(WalletBase):
    pass

class WalletOut(WalletBase):
    id: UUID  # 👈 trước là str, đổi sang UUID

    class Config:
        orm_mode = True
        # nếu dùng Pydantic v2 thì nên:
        # from_attributes = True
