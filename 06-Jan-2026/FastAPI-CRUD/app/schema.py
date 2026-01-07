from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    age: int

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
