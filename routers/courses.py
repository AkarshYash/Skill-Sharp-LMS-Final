from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import os, shutil, uuid, json

from database import get_db
from auth_utils import get_current_user, require_role
from config import settings
import models

router = APIRouter()

# ─── Schemas ───────────────────────────────
class CourseCreate(BaseModel):
    title: str
    description: str
    short_desc: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    level: str = "beginner"
    price: float = 0
    language: str = "English"
    student_type: Optional[str] = None
    class_grade: Optional[str] = None
    tags: List[str] = []
    what_you_learn: List[str] = []
    requirements: List[str] = []
    promo_video_url: Optional[str] = None

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    short_desc: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    level: Optional[str] = None
    price: Optional[float] = None
    language: Optional[str] = None
    tags: Optional[List[str]] = None
    what_you_learn: Optional[List[str]] = None
    requirements: Optional[List[str]] = None

class ApprovalAction(BaseModel):
    status: str   # approved / rejected
    note: Optional[str] = None

def course_dict(c: models.Course, include_faculty: bool = True) -> dict:
    data = {
        "id":             c.id,
        "title":          c.title,
        "description":    c.description,
        "short_desc":     c.short_desc,
        "category":       c.category,
        "subcategory":    c.subcategory,
        "level":          c.level,
        "price":          c.price,
        "thumbnail":      c.thumbnail,
        "promo_video_url": c.promo_video_url,
        "language":       c.language,
        "duration_hours": c.duration_hours,
        "is_published":   c.is_published,
        "is_featured":    c.is_featured,
        "approval_status": c.approval_status,
        "approval_note":  c.approval_note,
        "rating":         c.rating,
        "total_students": c.total_students,
        "total_lectures": c.total_lectures,
        "tags":           c.tags or [],
        "what_you_learn": c.what_you_learn or [],
        "requirements":   c.requirements or [],
        "student_type":   c.student_type,
        "class_grade":    c.class_grade,
        "created_at":     str(c.created_at),
        "faculty_id":     c.faculty_id,
    }
    if include_faculty and c.faculty:
        data["faculty"] = {
            "id":     c.faculty.id,
            "name":   c.faculty.name,
            "avatar": c.faculty.avatar,
            "expertise": c.faculty.expertise,
        }
    return data

# ─── Routes ────────────────────────────────

@router.get("/")
def list_courses(
    search: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    price_max: Optional[float] = None,
    student_type: Optional[str] = None,
    class_grade: Optional[str] = None,
    featured: Optional[bool] = None,
    page: int = 1,
    limit: int = 12,
    db: Session = Depends(get_db)
):
    q = db.query(models.Course).filter(
        models.Course.is_published == True,
        models.Course.approval_status == "approved"
    )
    if search:
        q = q.filter(
            models.Course.title.ilike(f"%{search}%") |
            models.Course.description.ilike(f"%{search}%")
        )
    if category:
        q = q.filter(models.Course.category == category)
    if level:
        q = q.filter(models.Course.level == level)
    if price_max is not None:
        q = q.filter(models.Course.price <= price_max)
    if student_type:
        q = q.filter(models.Course.student_type == student_type)
    if class_grade:
        q = q.filter(models.Course.class_grade == class_grade)
    if featured is not None:
        q = q.filter(models.Course.is_featured == featured)
    
    total = q.count()
    courses = q.order_by(models.Course.rating.desc()).offset((page-1)*limit).limit(limit).all()
    
    return {"total": total, "page": page, "courses": [course_dict(c) for c in courses]}

@router.post("/")
def create_course(
    data: CourseCreate,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    course = models.Course(
        title          = data.title,
        description    = data.description,
        short_desc     = data.short_desc,
        category       = data.category,
        subcategory    = data.subcategory,
        level          = data.level,
        price          = data.price,
        language       = data.language,
        faculty_id     = user.id,
        student_type   = data.student_type,
        class_grade    = data.class_grade,
        tags           = data.tags,
        what_you_learn = data.what_you_learn,
        requirements   = data.requirements,
        promo_video_url= data.promo_video_url,
        approval_status = "approved" if user.role == "admin" else "pending"
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course_dict(course)

@router.get("/my-courses")
def my_courses(
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    courses = db.query(models.Course).filter(models.Course.faculty_id == user.id).all()
    return [course_dict(c) for c in courses]

@router.get("/pending-approval")
def pending_courses(
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    courses = db.query(models.Course).filter(
        models.Course.approval_status == "pending"
    ).all()
    return [course_dict(c) for c in courses]

@router.get("/enrolled")
def my_enrolled_courses(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == user.id
    ).all()
    result = []
    for e in enrollments:
        cd = course_dict(e.course)
        cd["progress"] = e.progress
        cd["completed"] = e.completed
        cd["enrolled_at"] = str(e.enrolled_at)
        result.append(cd)
    return result

@router.get("/{course_id}")
def get_course(course_id: str, db: Session = Depends(get_db)):
    c = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not c:
        raise HTTPException(404, "Course not found")
    
    data = course_dict(c)
    data["lectures"] = [
        {
            "id":        l.id,
            "title":     l.title,
            "duration":  l.duration,
            "order_index": l.order_index,
            "is_preview": l.is_preview,
            "video_type": l.video_type,
        }
        for l in sorted(c.lectures, key=lambda x: x.order_index)
        if l.is_published
    ]
    data["reviews"] = [
        {
            "id":      r.id,
            "rating":  r.rating,
            "comment": r.comment,
            "created_at": str(r.created_at)
        }
        for r in c.reviews[-10:]
    ]
    return data

@router.put("/{course_id}")
def update_course(
    course_id: str,
    data: CourseUpdate,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    c = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not c:
        raise HTTPException(404, "Course not found")
    if user.role != "admin" and c.faculty_id != user.id:
        raise HTTPException(403, "Not your course")
    
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(c, field, value)
    
    # Re-submit for approval if faculty updates
    if user.role == "faculty":
        c.approval_status = "pending"
    
    db.commit()
    return course_dict(c)

@router.delete("/{course_id}")
def delete_course(
    course_id: str,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    c = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not c:
        raise HTTPException(404, "Course not found")
    if user.role != "admin" and c.faculty_id != user.id:
        raise HTTPException(403, "Not your course")
    db.delete(c)
    db.commit()
    return {"message": "Course deleted"}

@router.post("/{course_id}/thumbnail")
async def upload_thumbnail(
    course_id: str,
    file: UploadFile = File(...),
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    c = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not c:
        raise HTTPException(404, "Course not found")
    if user.role != "admin" and c.faculty_id != user.id:
        raise HTTPException(403, "Not your course")
    
    ext = file.filename.split(".")[-1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    path = f"static/uploads/thumbnails/{filename}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    c.thumbnail = f"/static/uploads/thumbnails/{filename}"
    db.commit()
    return {"thumbnail": c.thumbnail}

@router.post("/{course_id}/publish")
def toggle_publish(
    course_id: str,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    c = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not c:
        raise HTTPException(404, "Course not found")
    if user.role != "admin" and c.faculty_id != user.id:
        raise HTTPException(403, "Not your course")
    if c.approval_status != "approved" and user.role != "admin":
        raise HTTPException(400, "Course must be approved before publishing")
    
    c.is_published = not c.is_published
    db.commit()
    return {"is_published": c.is_published}

@router.post("/{course_id}/approve")
def approve_course(
    course_id: str,
    data: ApprovalAction,
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    c = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not c:
        raise HTTPException(404, "Course not found")
    if data.status not in ["approved", "rejected"]:
        raise HTTPException(400, "Invalid status")
    
    c.approval_status = data.status
    c.approval_note   = data.note
    if data.status == "approved":
        c.is_published = True
    
    # Notify faculty
    notif = models.Notification(
        user_id = c.faculty_id,
        title   = f"Course {data.status.capitalize()}",
        message = f"Your course '{c.title}' has been {data.status}" + (f": {data.note}" if data.note else ""),
        type    = "course"
    )
    db.add(notif)
    db.commit()
    return course_dict(c)

@router.post("/{course_id}/enroll")
def enroll(
    course_id: str,
    user: models.User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    c = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not c or not c.is_published:
        raise HTTPException(404, "Course not found")
    
    existing = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == user.id,
        models.Enrollment.course_id  == course_id
    ).first()
    if existing:
        raise HTTPException(400, "Already enrolled")
    
    enrollment = models.Enrollment(student_id=user.id, course_id=course_id)
    db.add(enrollment)
    c.total_students += 1
    
    # Award XP for enrollment
    pts = user.points
    if pts:
        pts.xp += 10
    
    db.commit()
    return {"message": "Enrolled successfully", "enrollment_id": enrollment.id}

@router.post("/{course_id}/review")
def add_review(
    course_id: str,
    rating: int,
    comment: str,
    user: models.User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == user.id,
        models.Enrollment.course_id  == course_id
    ).first()
    if not enrollment:
        raise HTTPException(403, "Must be enrolled to review")
    
    existing = db.query(models.Review).filter(
        models.Review.student_id == user.id,
        models.Review.course_id  == course_id
    ).first()
    if existing:
        existing.rating  = rating
        existing.comment = comment
    else:
        review = models.Review(course_id=course_id, student_id=user.id, rating=rating, comment=comment)
        db.add(review)
    
    # Update course rating
    reviews = db.query(models.Review).filter(models.Review.course_id == course_id).all()
    c = db.query(models.Course).filter(models.Course.id == course_id).first()
    c.rating = sum(r.rating for r in reviews) / len(reviews)
    
    db.commit()
    return {"message": "Review added", "new_rating": c.rating}

@router.get("/categories/list")
def get_categories(db: Session = Depends(get_db)):
    cats = db.query(models.Course.category).distinct().all()
    return [c[0] for c in cats if c[0]]
