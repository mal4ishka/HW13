from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class ContactBase(BaseModel):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: str = Field(max_length=50)
    phone: str = Field(max_length=50)
    birthday: str = Field(max_length=50)


class ContactResponse(ContactBase):
    class Config:
        from_attributes = True
        exclude_unset = True


class UserModel(BaseModel):
    username: str = Field(min_length=5, max_length=16)
    email: str
    password: str = Field(min_length=6, max_length=10)

    class Config:
        from_attributes = True

    def __iter__(self):
        yield self


class UserDb(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    avatar: str

    class Config:
        from_attributes = True

    def __iter__(self):
        yield self


class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"

    def __iter__(self):
        yield self


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr
