from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from auth_utils import get_current_user, require_role
import models

router = APIRouter()

class LiveClassCreate(BaseModel):
    course_id:        str
    title:            str
    description:      Optional[str] = None
    scheduled_at:     str   # ISO format
    duration_minutes: int = 60
    platform:         str = "jitsi"
    meeting_url:      Optional[str] = None
    meeting_id:       Optional[str] = None
    meeting_password: Optional[str] = None

class LiveClassUpdate(BaseModel):
    title:            Optional[str] = None
    description:      Optional[str] = None
    scheduled_at:     Optional[str] = None
    meeting_url:      Optional[str] = None
    meeting_id:       Optional[str] = None
    meeting_password: Optional[str] = None
    status:           Optional[str] = None
    recording_url:    Optional[str] = None

def live_class_dict(lc: models.LiveClass) -> dict:
    return {
        "id":               lc.id,
        "course_id":        lc.course_id,
        "faculty_id":       lc.faculty_id,
        "title":            lc.title,
        "description":      lc.description,
        "scheduled_at":     str(lc.scheduled_at),
        "duration_minutes": lc.duration_minutes,
        "platform":         lc.platform,
        "meeting_url":      lc.meeting_url,
        "meeting_id":       lc.meeting_id,
        "status":           lc.status,
        "recording_url":    lc.recording_url,
        "created_at":       str(lc.created_at),
    }

@router.get("/")
def get_live_classes(
    course_id: Optional[str] = None,
    status: Optional[str] = None,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(models.LiveClass)
    
    if user.role == "student":
        # Only show live classes from enrolled courses
        enrolled_ids = [e.course_id for e in db.query(models.Enrollment).filter(
            models.Enrollment.student_id == user.id
        ).all()]
        q = q.filter(models.LiveClass.course_id.in_(enrolled_ids))
    elif user.role == "faculty":
        q = q.filter(models.LiveClass.faculty_id == user.id)
    
    if course_id:
        q = q.filter(models.LiveClass.course_id == course_id)
    if status:
        q = q.filter(models.LiveClass.status == status)
    
    classes = q.order_by(models.LiveClass.scheduled_at.desc()).all()
    result = []
    for lc in classes:
        d = live_class_dict(lc)
        if lc.course:
            d["course_title"] = lc.course.title
        if lc.faculty_id:
            faculty = db.query(models.User).filter(models.User.id == lc.faculty_id).first()
            d["faculty_name"] = faculty.name if faculty else "Unknown"
        result.append(d)
    return result

@router.post("/")
def create_live_class(
    data: LiveClassCreate,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    try:
        scheduled = datetime.fromisoformat(data.scheduled_at)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Date & Time provided.")

    
    import uuid
    import re
    
    # Auto-generate Jitsi Meet link if requested
    if data.platform.lower() == "jitsi" and not data.meeting_url:
        room_name = re.sub(r'[^a-zA-Z0-9]', '', data.title) + str(uuid.uuid4())[:8]
        data.meeting_url = f"https://meet.jit.si/{room_name}"
        
    lc = models.LiveClass(
        course_id        = data.course_id,
        faculty_id       = user.id,
        title            = data.title,
        description      = data.description,
        scheduled_at     = scheduled,
        duration_minutes = data.duration_minutes,
        platform         = data.platform,
        meeting_url      = data.meeting_url,
        meeting_id       = data.meeting_id,
        meeting_password = data.meeting_password,
    )
    db.add(lc)
    
    # Notify enrolled students
    enrolled = db.query(models.Enrollment).filter(models.Enrollment.course_id == data.course_id).all()
    for e in enrolled:
        notif = models.Notification(
            user_id = e.student_id,
            title   = "📹 Live Class Scheduled",
            message = f"'{data.title}' is scheduled for {scheduled.strftime('%b %d, %Y at %I:%M %p')}",
            type    = "live_class",
            data    = {"live_class_id": lc.id, "course_id": data.course_id}
        )
        db.add(notif)
    
    db.commit()
    db.refresh(lc)
    return live_class_dict(lc)

@router.put("/{class_id}")
def update_live_class(
    class_id: str,
    data: LiveClassUpdate,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    lc = db.query(models.LiveClass).filter(models.LiveClass.id == class_id).first()
    if not lc:
        raise HTTPException(404, "Live class not found")
    if user.role != "admin" and lc.faculty_id != user.id:
        raise HTTPException(403, "Not your class")
    
    for field, value in data.model_dump(exclude_none=True).items():
        if field == "scheduled_at":
            value = datetime.fromisoformat(value)
        setattr(lc, field, value)
    
    db.commit()
    return live_class_dict(lc)

@router.delete("/{class_id}")
def delete_live_class(
    class_id: str,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    lc = db.query(models.LiveClass).filter(models.LiveClass.id == class_id).first()
    if not lc:
        raise HTTPException(404, "Not found")
    if user.role != "admin" and lc.faculty_id != user.id:
        raise HTTPException(403, "Not your class")
    db.delete(lc)
    db.commit()
    return {"message": "Deleted"}

@router.get("/upcoming")
def upcoming_classes(
    limit: int = 5,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()
    q   = db.query(models.LiveClass).filter(
        models.LiveClass.scheduled_at >= now,
        models.LiveClass.status       == "scheduled"
    )
    if user.role == "student":
        enrolled_ids = [e.course_id for e in db.query(models.Enrollment).filter(
            models.Enrollment.student_id == user.id
        ).all()]
        q = q.filter(models.LiveClass.course_id.in_(enrolled_ids))
    elif user.role == "faculty":
        q = q.filter(models.LiveClass.faculty_id == user.id)
    
    classes = q.order_by(models.LiveClass.scheduled_at.asc()).limit(limit).all()
    return [live_class_dict(lc) for lc in classes]
