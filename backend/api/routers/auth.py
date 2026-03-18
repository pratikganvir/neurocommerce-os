"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
import secrets
import string

from ..database import get_db
from ..security import hash_password, verify_password, create_access_token
from ..config import (
    STORE_ID_PREFIX, USER_ID_PREFIX, DEFAULT_USER_ROLE, 
    DEFAULT_ADMIN_ROLE, TOKEN_TYPE
)
from ...models.models import Store, User

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    store_id: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    store_name: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """User login"""
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create token
    access_token = create_access_token({"user_id": user.id, "store_id": user.store_id})
    
    return LoginResponse(
        access_token=access_token,
        token_type=TOKEN_TYPE,
        user_id=user.id,
        store_id=user.store_id
    )


@router.post("/register", response_model=LoginResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """User registration"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create store
    store_id = f"{STORE_ID_PREFIX}{secrets.token_urlsafe(16)}"
    new_store = Store(
        id=store_id,
        domain=request.email.split("@")[1],  # Use domain from email
        name=request.store_name,
        shopify_store_id=f"shopify_{secrets.token_urlsafe(8)}",
        shopify_access_token="",  # Will be set during Shopify OAuth
    )
    
    db.add(new_store)
    db.commit()
    
    # Create user
    user_id = f"{USER_ID_PREFIX}{secrets.token_urlsafe(16)}"
    new_user = User(
        id=user_id,
        store_id=store_id,
        email=request.email,
        name=request.name,
        password_hash=hash_password(request.password),
        role=DEFAULT_ADMIN_ROLE,  # First user is admin
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create token
    access_token = create_access_token({"user_id": user_id, "store_id": store_id})
    
    return LoginResponse(
        access_token=access_token,
        token_type=TOKEN_TYPE,
        user_id=user_id,
        store_id=store_id
    )
