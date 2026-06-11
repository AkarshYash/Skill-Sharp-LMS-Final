from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import pyotp, qrcode, io, base64

from database import get_db
from auth_utils import hash_password, verify_password, create_access_token, create_refresh_token, get_current_user
from config import settings
import models

router = APIRouter()

# ─── Schemas ───────────────────────────────
class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "student"
    student_type: Optional[str] = None
    class_grade: Optional[str] = None
    expertise: Optional[str] = None

class LoginSchema(BaseModel):
    email: EmailStr
    password: str
    two_fa_code: Optional[str] = None

class GoogleLoginSchema(BaseModel):
    email: EmailStr
    name: str
    google_id: str
    avatar: Optional[str] = None

class RefreshSchema(BaseModel):
    refresh_token: str

class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str

# ─── Routes ────────────────────────────────

@router.post("/register")
def register(data: RegisterSchema, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    
    allowed_roles = ["student", "faculty"]
    if data.role not in allowed_roles:
        data.role = "student"
    
    user = models.User(
        name         = data.name,
        email        = data.email,
        password     = hash_password(data.password),
        role         = data.role,
        student_type = data.student_type,
        class_grade  = data.class_grade,
        expertise    = data.expertise,
        is_verified  = True  # Auto-verify for demo
    )
    db.add(user)
    
    # Initialize points
    points = models.UserPoints(user_id=user.id)
    db.add(points)
    
    db.commit()
    db.refresh(user)
    
    access  = create_access_token(user.id, user.role)
    refresh = create_refresh_token(user.id)
    user.refresh_token = refresh
    db.commit()
    
    return {
        "access_token":  access,
        "refresh_token": refresh,
        "token_type":    "bearer",
        "user": {
            "id":    user.id,
            "name":  user.name,
            "email": user.email,
            "role":  user.role,
            "avatar": user.avatar
        }
    }

@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(401, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(403, "Account disabled")
    
    # 2FA check
    if user.two_fa_enabled:
        if not data.two_fa_code:
            return {"requires2FA": True, "message": "Please provide 2FA code"}
        totp = pyotp.TOTP(user.two_fa_secret)
        if not totp.verify(data.two_fa_code):
            raise HTTPException(401, "Invalid 2FA code")
    
    user.last_login = datetime.utcnow()
    
    access  = create_access_token(user.id, user.role)
    refresh = create_refresh_token(user.id)
    user.refresh_token = refresh
    db.commit()
    
    return {
        "access_token":  access,
        "refresh_token": refresh,
        "token_type":    "bearer",
        "user": {
            "id":        user.id,
            "name":      user.name,
            "email":     user.email,
            "role":      user.role,
            "avatar":    user.avatar,
            "two_fa_enabled": user.two_fa_enabled
        }
    }

@router.post("/google-login")
def google_login(data: GoogleLoginSchema, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    
    if not user:
        # Auto-register
        user = models.User(
            name         = data.name,
            email        = data.email,
            password     = hash_password(data.google_id), # Mock password
            role         = "student",
            avatar       = data.avatar,
            is_verified  = True
        )
        db.add(user)
        points = models.UserPoints(user_id=user.id)
        db.add(points)
        db.commit()
        db.refresh(user)
    
    if not user.is_active:
        raise HTTPException(403, "Account disabled")
        
    user.last_login = datetime.utcnow()
    
    access  = create_access_token(user.id, user.role)
    refresh = create_refresh_token(user.id)
    user.refresh_token = refresh
    db.commit()
    
    return {
        "access_token":  access,
        "refresh_token": refresh,
        "token_type":    "bearer",
        "user": {
            "id":        user.id,
            "name":      user.name,
            "email":     user.email,
            "role":      user.role,
            "avatar":    user.avatar,
            "two_fa_enabled": user.two_fa_enabled
        }
    }

@router.post("/refresh")
def refresh_token(data: RefreshSchema, db: Session = Depends(get_db)):
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(data.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
    except JWTError:
        raise HTTPException(401, "Invalid token")
    
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.refresh_token == data.refresh_token
    ).first()
    if not user:
        raise HTTPException(401, "Token revoked")
    
    access = create_access_token(user.id, user.role)
    return {"access_token": access, "token_type": "bearer"}

@router.post("/logout")
def logout(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.refresh_token = None
    db.commit()
    return {"message": "Logged out successfully"}

@router.get("/me")
def get_me(user: models.User = Depends(get_current_user)):
    return {
        "id":          user.id,
        "name":        user.name,
        "email":       user.email,
        "role":        user.role,
        "avatar":      user.avatar,
        "bio":         user.bio,
        "phone":       user.phone,
        "expertise":   user.expertise,
        "student_type": user.student_type,
        "class_grade": user.class_grade,
        "linkedin_url": user.linkedin_url,
        "github_url":  user.github_url,
        "two_fa_enabled": user.two_fa_enabled,
        "is_verified": user.is_verified,
        "created_at":  str(user.created_at)
    }

@router.post("/change-password")
def change_password(
    data: ChangePasswordSchema,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(data.old_password, user.password):
        raise HTTPException(400, "Incorrect old password")
    user.password = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@router.post("/2fa/setup")
def setup_2fa(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = pyotp.random_base32()
    user.two_fa_secret = secret
    db.commit()
    
    totp = pyotp.TOTP(secret)
    uri  = totp.provisioning_uri(name=user.email, issuer_name="EduAI Platform")
    
    # Generate QR code
    qr_img = qrcode.make(uri)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    
    return {"secret": secret, "qr_code": f"data:image/png;base64,{qr_b64}"}

@router.post("/2fa/enable")
def enable_2fa(
    code: str = Body(..., embed=True),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user.two_fa_secret:
        raise HTTPException(400, "Setup 2FA first")
    totp = pyotp.TOTP(user.two_fa_secret)
    if not totp.verify(code):
        raise HTTPException(400, "Invalid code")
    user.two_fa_enabled = True
    db.commit()
    return {"message": "2FA enabled successfully"}

@router.post("/2fa/disable")
def disable_2fa(
    code: str = Body(..., embed=True),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user.two_fa_enabled:
        raise HTTPException(400, "2FA not enabled")
    totp = pyotp.TOTP(user.two_fa_secret)
    if not totp.verify(code):
        raise HTTPException(400, "Invalid code")
    user.two_fa_enabled = False
    user.two_fa_secret  = None
    db.commit()
    return {"message": "2FA disabled successfully"}
