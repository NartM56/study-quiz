from pydantic import BaseModel, EmailStr


class SignUpRequest(BaseModel):
    """Request model for user sign-up"""
    email: EmailStr
    display_name: str
    password: str


class LoginRequest(BaseModel):
    """Request model for user login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response model for JWT token"""
    access_token: str
    token_type: str = "bearer"
