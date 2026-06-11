from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import os, shutil, uuid

from database import get_db
from auth_utils import get_current_user, require_role, hash_password
from config import settings
import models

router = APIRouter()

class UpdateProfileSchema(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    expertise: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    student_type: Optional[str] = None
    class_grade: Optional[str] = None

def user_dict(u: models.User, db: Session = None) -> dict:
    pts = u.points
    return {
        "id":          u.id,
        "name":        u.name,
        "email":       u.email,
        "role":        u.role,
        "avatar":      u.avatar,
        "bio":         u.bio,
        "phone":       u.phone,
        "expertise":   u.expertise,
        "student_type": u.student_type,
        "class_grade": u.class_grade,
        "linkedin_url": u.linkedin_url,
        "github_url":  u.github_url,
        "is_verified": u.is_verified,
        "is_active":   u.is_active,
        "created_at":  str(u.created_at),
        "last_login":  str(u.last_login) if u.last_login else None,
        "xp":          pts.xp if pts else 0,
        "level":       pts.level if pts else 1,
        "streak_days": pts.streak_days if pts else 0,
    }

@router.get("/profile")
def get_profile(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return user_dict(user, db)

@router.put("/profile")
def update_profile(
    data: UpdateProfileSchema,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    return {"message": "Profile updated", "user": user_dict(user, db)}

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(400, "Only jpg/jpeg/png/webp allowed")
    
    filename = f"{uuid.uuid4()}.{ext}"
    path = f"static/uploads/avatars/{filename}"
    
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    user.avatar = f"/static/uploads/avatars/{filename}"
    db.commit()
    return {"avatar": user.avatar}

@router.get("/list")
def list_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    q = db.query(models.User)
    if role:
        q = q.filter(models.User.role == role)
    if search:
        q = q.filter(models.User.name.ilike(f"%{search}%") | models.User.email.ilike(f"%{search}%"))
    
    total = q.count()
    users = q.offset((page-1)*limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "users": [user_dict(u, db) for u in users]
    }

@router.get("/{user_id}")
def get_user(
    user_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_id == "me":
        return user_dict(current_user, db)
    
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(403, "Forbidden")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user_dict(user, db)

@router.put("/{user_id}/toggle-active")
def toggle_user_active(
    user_id: str,
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User {'activated' if user.is_active else 'deactivated'}", "is_active": user.is_active}

@router.put("/{user_id}/role")
def change_role(
    user_id: str,
    role: str,
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    if role not in ["admin", "faculty", "student"]:
        raise HTTPException(400, "Invalid role")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.role = role
    db.commit()
    return {"message": "Role updated", "role": role}

@router.get("/stats/overview")
def user_stats(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enrollments = db.query(models.Enrollment).filter(models.Enrollment.student_id == user.id).all()
    completed   = [e for e in enrollments if e.completed]
    badges      = db.query(models.UserBadge).filter(models.UserBadge.user_id == user.id).count()
    certs       = db.query(models.Certificate).filter(models.Certificate.student_id == user.id).count()
    pts         = user.points
    
    return {
        "enrolled_courses":   len(enrollments),
        "completed_courses":  len(completed),
        "certificates":       certs,
        "badges":             badges,
        "xp":                 pts.xp if pts else 0,
        "level":              pts.level if pts else 1,
        "streak_days":        pts.streak_days if pts else 0,
    }
