from pydantic import BaseModel

class CategoryBase(BaseModel):
    name: str
    icon: str
    color: str | None = None

class CategoryCreate(CategoryBase):
    pass

class CategoryOut(CategoryBase):
    id: str
    class Config:
        orm_mode = True
