from pydantic import BaseModel

class WalletBase(BaseModel):
    balance: float

class WalletCreate(WalletBase):
    pass

class WalletOut(WalletBase):
    id: str
    class Config:
        orm_mode = True
