from pydantic import BaseModel, EmailStr, Field

class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone_number: str | None = None

# Pydantic модели
class User(BaseModel):
    username: str
    password_hash: str
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    phone_number: str | None = None
    role: str = "user"

class TestCategory(BaseModel):
    category_name: str

class TestType(BaseModel):
    type_name: str
    category_id: int

class Test(BaseModel):
    user_id: int
    type_id: int
    score: int = Field(..., ge=1, le=100)
    difficulty: str