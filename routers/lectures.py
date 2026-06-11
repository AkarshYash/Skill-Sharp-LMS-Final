from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import shutil, uuid, json

from database import get_db
from auth_utils import get_current_user, require_role
import models

router = APIRouter()

class LectureCreate(BaseModel):
    course_id:   str
    title:       str
    description: Optional[str] = None
    video_url:   Optional[str] = None
    video_type:  str = "youtube"
    duration:    int = 0
    order_index: int = 0
    is_preview:  bool = False

class LectureUpdate(BaseModel):
    title:       Optional[str] = None
    description: Optional[str] = None
    video_url:   Optional[str] = None
    video_type:  Optional[str] = None
    duration:    Optional[int] = None
    order_index: Optional[int] = None
    is_preview:  Optional[bool] = None
    is_published: Optional[bool] = None

def lecture_dict(l: models.Lecture) -> dict:
    return {
        "id":          l.id,
        "course_id":   l.course_id,
        "title":       l.title,
        "description": l.description,
        "video_url":   l.video_url,
        "video_type":  l.video_type,
        "duration":    l.duration,
        "order_index": l.order_index,
        "is_preview":  l.is_preview,
        "is_published": l.is_published,
        "resources":   l.resources or [],
        "ai_summary":  l.ai_summary,
        "created_at":  str(l.created_at),
        "notes": [
            {
                "id":       n.id,
                "filename": n.filename,
                "file_url": n.file_url,
                "file_type": n.file_type,
            }
            for n in l.notes
        ]
    }

@router.get("/course/{course_id}")
def get_course_lectures(
    course_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check enrollment or ownership
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(404, "Course not found")
    
    if user.role == "student":
        enrollment = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == user.id,
            models.Enrollment.course_id  == course_id
        ).first()
        if not enrollment:
            # Return only preview lectures
            lectures = [l for l in course.lectures if l.is_preview and l.is_published]
        else:
            lectures = [l for l in course.lectures if l.is_published]
    else:
        lectures = course.lectures
    
    return sorted([lecture_dict(l) for l in lectures], key=lambda x: x["order_index"])

@router.post("/")
def create_lecture(
    data: LectureCreate,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    course = db.query(models.Course).filter(models.Course.id == data.course_id).first()
    if not course:
        raise HTTPException(404, "Course not found")
    if user.role != "admin" and course.faculty_id != user.id:
        raise HTTPException(403, "Not your course")
    
    lecture = models.Lecture(
        course_id   = data.course_id,
        title       = data.title,
        description = data.description,
        video_url   = data.video_url,
        video_type  = data.video_type,
        duration    = data.duration,
        order_index = data.order_index,
        is_preview  = data.is_preview,
    )
    db.add(lecture)
    
    # Update course lecture count
    course.total_lectures = db.query(models.Lecture).filter(
        models.Lecture.course_id == data.course_id
    ).count() + 1
    
    db.commit()
    db.refresh(lecture)
    return lecture_dict(lecture)

@router.put("/{lecture_id}")
def update_lecture(
    lecture_id: str,
    data: LectureUpdate,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    lec = db.query(models.Lecture).filter(models.Lecture.id == lecture_id).first()
    if not lec:
        raise HTTPException(404, "Lecture not found")
    
    course = db.query(models.Course).filter(models.Course.id == lec.course_id).first()
    if user.role != "admin" and course.faculty_id != user.id:
        raise HTTPException(403, "Not your course")
    
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(lec, field, value)
    db.commit()
    return lecture_dict(lec)

@router.delete("/{lecture_id}")
def delete_lecture(
    lecture_id: str,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    lec = db.query(models.Lecture).filter(models.Lecture.id == lecture_id).first()
    if not lec:
        raise HTTPException(404, "Lecture not found")
    course = db.query(models.Course).filter(models.Course.id == lec.course_id).first()
    if user.role != "admin" and course.faculty_id != user.id:
        raise HTTPException(403, "Not your course")
    db.delete(lec)
    db.commit()
    return {"message": "Lecture deleted"}

@router.post("/{lecture_id}/notes")
async def upload_notes(
    lecture_id: str,
    file: UploadFile = File(...),
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    lec = db.query(models.Lecture).filter(models.Lecture.id == lecture_id).first()
    if not lec:
        raise HTTPException(404, "Lecture not found")
    course = db.query(models.Course).filter(models.Course.id == lec.course_id).first()
    if user.role != "admin" and course.faculty_id != user.id:
        raise HTTPException(403, "Not your course")
    
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "doc", "docx", "txt", "pptx"]:
        raise HTTPException(400, "Invalid file type")
    
    filename = f"{uuid.uuid4()}.{ext}"
    path = f"static/uploads/notes/{filename}"
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    
    note = models.LectureNote(
        lecture_id = lecture_id,
        course_id  = lec.course_id,
        faculty_id = user.id,
        filename   = file.filename,
        file_url   = f"/static/uploads/notes/{filename}",
        file_type  = ext,
        file_size  = len(content)
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    
    # Trigger RAG indexing in background (non-blocking)
    try:
        from services.rag_service import index_document
        index_document(note.id, path, lec.course_id, db)
    except Exception as e:
        print(f"RAG indexing failed: {e}")
    
    return {
        "id":       note.id,
        "filename": note.filename,
        "file_url": note.file_url,
        "is_indexed": note.is_indexed
    }

@router.post("/{lecture_id}/progress")
def update_progress(
    lecture_id: str,
    watched_sec: int,
    completed: bool = False,
    user: models.User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    lec = db.query(models.Lecture).filter(models.Lecture.id == lecture_id).first()
    if not lec:
        raise HTTPException(404, "Lecture not found")
    
    prog = db.query(models.LectureProgress).filter(
        models.LectureProgress.student_id == user.id,
        models.LectureProgress.lecture_id == lecture_id
    ).first()
    
    if not prog:
        prog = models.LectureProgress(
            student_id = user.id,
            lecture_id = lecture_id,
            course_id  = lec.course_id
        )
        db.add(prog)
    
    prog.watched_sec = watched_sec
    if completed and not prog.completed:
        prog.completed = True
        # Award XP
        pts = user.points
        if pts:
            pts.xp += 20
        
        # Update enrollment progress
        enrollment = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == user.id,
            models.Enrollment.course_id  == lec.course_id
        ).first()
        if enrollment:
            total = db.query(models.Lecture).filter(
                models.Lecture.course_id == lec.course_id,
                models.Lecture.is_published == True
            ).count()
            done = db.query(models.LectureProgress).filter(
                models.LectureProgress.student_id == user.id,
                models.LectureProgress.course_id  == lec.course_id,
                models.LectureProgress.completed   == True
            ).count()
            enrollment.progress = int((done / total * 100)) if total > 0 else 0
            if enrollment.progress >= 100:
                enrollment.completed = True
                from datetime import datetime
                enrollment.completed_at = datetime.utcnow()
    
    db.commit()
    return {"message": "Progress updated", "progress": prog.watched_sec, "completed": prog.completed}

@router.post("/{lecture_id}/ai-summary")
async def generate_ai_summary(
    lecture_id: str,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    lec = db.query(models.Lecture).filter(models.Lecture.id == lecture_id).first()
    if not lec:
        raise HTTPException(404, "Lecture not found")
    
    try:
        from services.ai_service import generate_lecture_summary
        summary = await generate_lecture_summary(lec.title, lec.description or "")
        lec.ai_summary = summary
        db.commit()
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(500, f"AI summary failed: {str(e)}")
