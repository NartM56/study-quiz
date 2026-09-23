from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):
    """Request model for user sign-up"""
    email: EmailStr = Field(max_length=255)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    """Request model for user login"""
    email: EmailStr = Field(max_length=255)
    password: str


class TokenResponse(BaseModel):
    """Response model for JWT token"""
    access_token: str
    token_type: str = "bearer"
