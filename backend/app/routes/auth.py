from fastapi import APIRouter, Depends, HTTPException          
from sqlalchemy.orm import Session
from app.db.database import get_db                             
from app.models.study_models import User                       
from app.schemas.auth import LoginRequest, SignUpRequest, TokenResponse                                                       
from app.services.security import create_access_token, hash_password, verify_password

router = APIRouter()

@router.post("/signup", response_model=TokenResponse, status_code=201)
def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email = request.email,
        display_name = request.display_name,
        password_hash = hash_password(request.password)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if not existing_user or not verify_password(request.password, existing_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(existing_user.id)
    return TokenResponse(access_token=token)