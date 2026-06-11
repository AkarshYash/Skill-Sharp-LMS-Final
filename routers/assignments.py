from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import shutil, uuid

from database import get_db
from auth_utils import get_current_user, require_role
import models

router = APIRouter()

class AssignmentCreate(BaseModel):
    course_id:   str
    title:       str
    description: str
    due_date:    str   # ISO format
    max_marks:   int = 100
    allow_late:  bool = False

class GradeSubmission(BaseModel):
    marks:    int
    feedback: str

@router.get("/course/{course_id}")
def get_assignments(
    course_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    assignments = db.query(models.Assignment).filter(models.Assignment.course_id == course_id).all()
    result = []
    for a in assignments:
        d = {
            "id":          a.id,
            "title":       a.title,
            "description": a.description,
            "due_date":    str(a.due_date),
            "max_marks":   a.max_marks,
            "allow_late":  a.allow_late,
            "file_url":    a.file_url,
        }
        if user.role == "student":
            sub = db.query(models.AssignmentSubmission).filter(
                models.AssignmentSubmission.assignment_id == a.id,
                models.AssignmentSubmission.student_id    == user.id
            ).first()
            d["my_submission"] = {
                "id":      sub.id,
                "marks":   sub.marks,
                "feedback": sub.feedback,
                "submitted_at": str(sub.submitted_at)
            } if sub else None
        else:
            d["submission_count"] = db.query(models.AssignmentSubmission).filter(
                models.AssignmentSubmission.assignment_id == a.id
            ).count()
        result.append(d)
    return result

@router.post("/")
def create_assignment(
    data: AssignmentCreate,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    due = datetime.fromisoformat(data.due_date)
    a = models.Assignment(
        course_id   = data.course_id,
        faculty_id  = user.id,
        title       = data.title,
        description = data.description,
        due_date    = due,
        max_marks   = data.max_marks,
        allow_late  = data.allow_late
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"id": a.id, "title": a.title, "due_date": str(a.due_date)}

@router.post("/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: str,
    content: Optional[str] = None,
    file: Optional[UploadFile] = File(None),
    user: models.User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(404, "Assignment not found")
    
    # Check existing submission
    existing = db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.assignment_id == assignment_id,
        models.AssignmentSubmission.student_id    == user.id
    ).first()
    
    file_url = None
    if file:
        ext = file.filename.split(".")[-1].lower()
        filename = f"{uuid.uuid4()}.{ext}"
        path = f"static/uploads/assignments/{filename}"
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        file_url = f"/static/uploads/assignments/{filename}"
    
    is_late = datetime.utcnow() > assignment.due_date
    
    if existing:
        existing.content  = content
        existing.file_url = file_url or existing.file_url
        existing.is_late  = is_late
        sub = existing
    else:
        sub = models.AssignmentSubmission(
            assignment_id = assignment_id,
            student_id    = user.id,
            content       = content,
            file_url      = file_url,
            is_late       = is_late
        )
        db.add(sub)
    
    db.commit()
    
    # Award XP for submission
    pts = user.points
    if pts:
        pts.xp += 15
        db.commit()
    
    return {"message": "Assignment submitted", "is_late": is_late}

@router.get("/{assignment_id}/submissions")
def get_submissions(
    assignment_id: str,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    subs = db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.assignment_id == assignment_id
    ).all()
    return [
        {
            "id":          s.id,
            "student_id":  s.student_id,
            "student_name": s.student.name if s.student else "Unknown",
            "content":     s.content,
            "file_url":    s.file_url,
            "marks":       s.marks,
            "feedback":    s.feedback,
            "is_late":     s.is_late,
            "submitted_at": str(s.submitted_at),
        }
        for s in subs
    ]

@router.post("/{assignment_id}/submissions/{submission_id}/grade")
async def grade_submission(
    assignment_id: str,
    submission_id: str,
    data: GradeSubmission,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    sub = db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.id            == submission_id,
        models.AssignmentSubmission.assignment_id == assignment_id
    ).first()
    if not sub:
        raise HTTPException(404, "Submission not found")
    
    sub.marks      = data.marks
    sub.feedback   = data.feedback
    sub.graded_by  = user.id
    from datetime import datetime
    sub.graded_at  = datetime.utcnow()
    
    # Notify student
    notif = models.Notification(
        user_id = sub.student_id,
        title   = "Assignment Graded",
        message = f"Your assignment has been graded: {data.marks} marks. {data.feedback[:100]}",
        type    = "assignment"
    )
    db.add(notif)
    
    # Award XP based on marks
    pts = db.query(models.UserPoints).filter(models.UserPoints.user_id == sub.student_id).first()
    if pts:
        xp = int(data.marks / 10) * 5
        pts.xp += xp
    
    db.commit()
    return {"message": "Graded successfully", "marks": sub.marks}

@router.post("/{assignment_id}/submissions/{submission_id}/ai-feedback")
async def ai_feedback(
    assignment_id: str,
    submission_id: str,
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    sub = db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.id == submission_id
    ).first()
    if not sub or not sub.content:
        raise HTTPException(404, "Submission not found or empty")
    
    try:
        from services.ai_service import generate_assignment_feedback
        feedback = await generate_assignment_feedback(sub.content)
        sub.ai_feedback = feedback
        db.commit()
        return {"ai_feedback": feedback}
    except Exception as e:
        raise HTTPException(500, f"AI feedback failed: {str(e)}")
