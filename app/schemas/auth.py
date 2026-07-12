from pydantic import BaseModel, EmailStr

from app.schemas.user import UserResponse


class SignupRequest(BaseModel):

    full_name: str

    email: EmailStr

    password: str


class LoginRequest(BaseModel):

    email: EmailStr

    password: str


class AuthResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    user: UserResponse