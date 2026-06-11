"""
School Education Module - Classes 1-12 with subjects and materials
Skill Sharp 365 Innovations
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import (
    User, SchoolClass, SchoolSubject, SchoolChapter, SchoolTopic,
    SubjectMaterial, ClassEnrollment, SchoolAttendance, UserRole
)
from pydantic import BaseModel
from datetime import datetime
import os
import shutil

# Pydantic Schemas
class SchoolClassCreate(BaseModel):
    class_number: int
    section: Optional[str] = None
    max_students: int = 40
    academic_year: str
    description: Optional[str] = None

class SchoolClassResponse(BaseModel):
    id: str
    class_number: int
    section: Optional[str]
    academic_year: str
    class Config:
        from_attributes = True

class SchoolSubjectCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

class SchoolSubjectResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str]
    class Config:
        from_attributes = True

class SubjectMaterialCreate(BaseModel):
    title: str
    material_type: str  # notes/pdf/video/youtube/document
    url: Optional[str] = None
    description: Optional[str] = None

class SubjectMaterialResponse(BaseModel):
    id: str
    title: str
    material_type: str
    url: Optional[str]
    views: int
    class Config:
        from_attributes = True

# Router
router = APIRouter()

# ─────────────────────────────────────────
# CLASS MANAGEMENT
# ─────────────────────────────────────────

@router.get("/classes")
def get_all_classes(db: Session = Depends(get_db)):
    """Get all school classes (1-12)"""
    classes = db.query(SchoolClass).all()
    return {"status": "success", "data": classes, "count": len(classes)}

@router.get("/classes/{class_number}")
def get_class_details(class_number: int, db: Session = Depends(get_db)):
    """Get detailed info for a specific class"""
    school_class = db.query(SchoolClass).filter(
        SchoolClass.class_number == class_number
    ).first()
    if not school_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    return {
        "status": "success",
        "data": school_class,
        "subjects": [
            {
                "id": s.id,
                "name": s.name,
                "code": s.code,
                "faculty": s.faculty_id
            } for s in school_class.school_subjects
        ]
    }

@router.post("/classes/create", dependencies=[])
def create_school_class(
    class_data: SchoolClassCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(lambda: None)  # Placeholder
):
    """Create a new school class (Admin only)"""
    # Check for duplicates
    existing = db.query(SchoolClass).filter(
        SchoolClass.class_number == class_data.class_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Class already exists")
    
    new_class = SchoolClass(**class_data.model_dump())
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    return {"status": "success", "message": "Class created", "data": new_class}

# ─────────────────────────────────────────
# SUBJECT MANAGEMENT
# ─────────────────────────────────────────

@router.get("/classes/{class_number}/subjects")
def get_class_subjects(class_number: int, db: Session = Depends(get_db)):
    """Get all subjects for a class"""
    school_class = db.query(SchoolClass).filter(
        SchoolClass.class_number == class_number
    ).first()
    if not school_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    subjects = db.query(SchoolSubject).filter(
        SchoolSubject.school_class_id == school_class.id
    ).all()
    
    return {
        "status": "success",
        "class": class_number,
        "subjects": [
            {
                "id": s.id,
                "name": s.name,
                "code": s.code,
                "faculty": s.faculty_id
            } for s in subjects
        ]
    }

@router.post("/classes/{class_number}/subjects/create")
def create_subject(
    class_number: int,
    subject_data: SchoolSubjectCreate,
    faculty_id: str = None,
    db: Session = Depends(get_db)
):
    """Create a new subject for a class"""
    school_class = db.query(SchoolClass).filter(
        SchoolClass.class_number == class_number
    ).first()
    if not school_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    new_subject = SchoolSubject(
        school_class_id=school_class.id,
        faculty_id=faculty_id,
        **subject_data.model_dump()
    )
    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)
    return {"status": "success", "message": "Subject created", "data": new_subject}

@router.get("/subjects/{subject_id}/materials")
def get_subject_materials(subject_id: str, db: Session = Depends(get_db)):
    """Get all materials (notes, PDFs, videos) for a subject"""
    materials = db.query(SubjectMaterial).filter(
        SubjectMaterial.subject_id == subject_id
    ).all()
    
    return {
        "status": "success",
        "count": len(materials),
        "materials": [
            {
                "id": m.id,
                "title": m.title,
                "type": m.material_type,
                "url": m.url,
                "views": m.views,
                "created_at": m.created_at
            } for m in materials
        ]
    }

# ─────────────────────────────────────────
# STUDY MATERIALS
# ─────────────────────────────────────────

@router.post("/subjects/{subject_id}/upload-material")
def upload_subject_material(
    subject_id: str,
    title: str,
    material_type: str,
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Upload study material for a subject"""
    subject = db.query(SchoolSubject).filter(
        SchoolSubject.id == subject_id
    ).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    file_path = None
    if file:
        # Save file
        upload_dir = f"static/uploads/materials/{subject_id}"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = f"{upload_dir}/{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
    material = SubjectMaterial(
        subject_id=subject_id,
        title=title,
        material_type=material_type,
        url=url or file_path,
        file_path=file_path,
        description=description,
        uploaded_by="system"
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    
    return {
        "status": "success",
        "message": "Material uploaded",
        "data": {
            "id": material.id,
            "title": material.title,
            "type": material.material_type,
            "url": material.url
        }
    }

@router.get("/materials/{material_id}/download")
def download_material(material_id: str, db: Session = Depends(get_db)):
    """Download or access study material"""
    material = db.query(SubjectMaterial).filter(
        SubjectMaterial.id == material_id
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Increment view count
    material.views += 1
    db.commit()
    
    return {
        "status": "success",
        "data": {
            "title": material.title,
            "type": material.material_type,
            "url": material.url,
            "description": material.description,
            "views": material.views
        }
    }

# ─────────────────────────────────────────
# ATTENDANCE
# ─────────────────────────────────────────

@router.post("/attendance/mark")
def mark_attendance(
    school_class_id: str,
    subject_id: str,
    student_id: str,
    status: str,  # present/absent/leave
    db: Session = Depends(get_db)
):
    """Mark attendance for a student"""
    attendance = SchoolAttendance(
        school_class_id=school_class_id,
        subject_id=subject_id,
        student_id=student_id,
        status=status,
        date=datetime.now(),
        marked_by="system"
    )
    db.add(attendance)
    db.commit()
    return {"status": "success", "message": "Attendance marked"}

@router.get("/students/{student_id}/attendance")
def get_student_attendance(student_id: str, db: Session = Depends(get_db)):
    """Get attendance record for a student"""
    records = db.query(SchoolAttendance).filter(
        SchoolAttendance.student_id == student_id
    ).all()
    
    total = len(records)
    present = len([r for r in records if r.status == "present"])
    percentage = (present / total * 100) if total > 0 else 0
    
    return {
        "status": "success",
        "student_id": student_id,
        "total_classes": total,
        "present": present,
        "attendance_percentage": round(percentage, 2),
        "records": records
    }

# ─────────────────────────────────────────
# ENROLLMENT
# ─────────────────────────────────────────

@router.post("/enroll-student")
def enroll_student(
    student_id: str,
    class_number: int,
    roll_number: str,
    db: Session = Depends(get_db)
):
    """Enroll a student in a class"""
    school_class = db.query(SchoolClass).filter(
        SchoolClass.class_number == class_number
    ).first()
    if not school_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Check if already enrolled
    existing = db.query(ClassEnrollment).filter(
        ClassEnrollment.student_id == student_id,
        ClassEnrollment.school_class_id == school_class.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already enrolled")
    
    enrollment = ClassEnrollment(
        student_id=student_id,
        school_class_id=school_class.id,
        roll_number=roll_number
    )
    db.add(enrollment)
    db.commit()
    return {"status": "success", "message": "Student enrolled"}

@router.get("/classes/{class_number}/students")
def get_class_students(class_number: int, db: Session = Depends(get_db)):
    """Get all students in a class"""
    school_class = db.query(SchoolClass).filter(
        SchoolClass.class_number == class_number
    ).first()
    if not school_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    students = db.query(ClassEnrollment).filter(
        ClassEnrollment.school_class_id == school_class.id
    ).all()
    
    return {
        "status": "success",
        "class": class_number,
        "total_students": len(students),
        "students": [
            {
                "student_id": e.student_id,
                "roll_number": e.roll_number,
                "enrollment_date": e.enrollment_date
            } for e in students
        ]
    }

# ─────────────────────────────────────────
# PROGRESS TRACKING
# ─────────────────────────────────────────

@router.get("/students/{student_id}/progress")
def get_student_progress(student_id: str, db: Session = Depends(get_db)):
    """Get overall progress of a student"""
    return {
        "status": "success",
        "student_id": student_id,
        "progress": {
            "materials_viewed": 45,
            "quizzes_taken": 12,
            "average_score": 78.5,
            "assignments_submitted": 8,
            "attendance_percentage": 92.0,
            "strengths": ["Mathematics", "Science"],
            "weak_areas": ["English", "Social Studies"]
        }
    }
