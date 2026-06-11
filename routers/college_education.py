"""
College Education Module - Programs, Semesters, Courses
Skill Sharp 365 Innovations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import (
    EducationStream, DegreeProgram, Semester, CollegeCourseSubject,
    CollegeMaterial, ProgramEnrollment, User
)
from pydantic import BaseModel
from datetime import datetime

class ProgramResponse(BaseModel):
    id: str
    name: str
    code: str
    duration_years: int
    total_semesters: int
    class Config:
        from_attributes = True

router = APIRouter()

# ─────────────────────────────────────────
# STREAMS & PROGRAMS
# ─────────────────────────────────────────

@router.get("/streams")
def get_education_streams(db: Session = Depends(get_db)):
    """Get all education streams (Science, Commerce, Arts, Law, Medical)"""
    streams = db.query(EducationStream).all()
    return {
        "status": "success",
        "streams": [
            {"id": s.id, "name": s.name, "description": s.description}
            for s in streams
        ]
    }

@router.get("/streams/{stream_id}/programs")
def get_stream_programs(stream_id: str, db: Session = Depends(get_db)):
    """Get all degree programs in a stream"""
    programs = db.query(DegreeProgram).filter(
        DegreeProgram.stream_id == stream_id
    ).all()
    
    return {
        "status": "success",
        "programs": [
            {
                "id": p.id,
                "name": p.name,
                "code": p.code,
                "duration": f"{p.duration_years} years",
                "semesters": p.total_semesters,
                "specializations": p.specializations
            } for p in programs
        ]
    }

@router.get("/programs/{program_id}")
def get_program_details(program_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a degree program"""
    program = db.query(DegreeProgram).filter(
        DegreeProgram.id == program_id
    ).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    return {
        "status": "success",
        "program": {
            "id": program.id,
            "name": program.name,
            "code": program.code,
            "duration": program.duration_years,
            "semesters": program.total_semesters,
            "specializations": program.specializations,
            "description": program.description
        }
    }

# ─────────────────────────────────────────
# SEMESTERS & SUBJECTS
# ─────────────────────────────────────────

@router.get("/programs/{program_id}/semesters")
def get_program_semesters(program_id: str, db: Session = Depends(get_db)):
    """Get all semesters in a program"""
    semesters = db.query(Semester).filter(
        Semester.program_id == program_id
    ).order_by(Semester.semester_num).all()
    
    return {
        "status": "success",
        "semesters": [
            {
                "id": s.id,
                "number": s.semester_num,
                "title": s.title,
                "description": s.description
            } for s in semesters
        ]
    }

@router.get("/semesters/{semester_id}/subjects")
def get_semester_subjects(semester_id: str, db: Session = Depends(get_db)):
    """Get all subjects in a semester"""
    subjects = db.query(CollegeCourseSubject).filter(
        CollegeCourseSubject.semester_id == semester_id
    ).all()
    
    return {
        "status": "success",
        "subjects": [
            {
                "id": s.id,
                "code": s.code,
                "name": s.name,
                "credits": s.credits,
                "faculty": s.faculty_id
            } for s in subjects
        ]
    }

@router.get("/subjects/{subject_id}")
def get_subject_details(subject_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a subject"""
    subject = db.query(CollegeCourseSubject).filter(
        CollegeCourseSubject.id == subject_id
    ).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Get materials
    materials = db.query(CollegeMaterial).filter(
        CollegeMaterial.subject_id == subject_id
    ).all()
    
    return {
        "status": "success",
        "subject": {
            "id": subject.id,
            "code": subject.code,
            "name": subject.name,
            "credits": subject.credits,
            "description": subject.description
        },
        "materials": [
            {
                "id": m.id,
                "title": m.title,
                "type": m.material_type,
                "url": m.url,
                "views": m.views
            } for m in materials
        ]
    }

@router.get("/subjects/{subject_id}/materials")
def get_subject_materials(subject_id: str, db: Session = Depends(get_db)):
    """Get all learning materials for a subject"""
    materials = db.query(CollegeMaterial).filter(
        CollegeMaterial.subject_id == subject_id
    ).all()
    
    return {
        "status": "success",
        "total": len(materials),
        "materials_by_type": {
            "notes": [m for m in materials if m.material_type == "notes"],
            "books": [m for m in materials if m.material_type == "book"],
            "videos": [m for m in materials if m.material_type == "video"],
            "labs": [m for m in materials if m.material_type == "lab"],
            "pdfs": [m for m in materials if m.material_type == "pdf"]
        }
    }

# ─────────────────────────────────────────
# ENROLLMENT
# ─────────────────────────────────────────

@router.post("/enroll-program")
def enroll_in_program(
    student_id: str,
    program_id: str,
    admission_number: str,
    enrollment_year: int,
    db: Session = Depends(get_db)
):
    """Enroll a student in a degree program"""
    program = db.query(DegreeProgram).filter(
        DegreeProgram.id == program_id
    ).first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    # Check for duplicate enrollment
    existing = db.query(ProgramEnrollment).filter(
        ProgramEnrollment.student_id == student_id,
        ProgramEnrollment.program_id == program_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already enrolled")
    
    enrollment = ProgramEnrollment(
        student_id=student_id,
        program_id=program_id,
        admission_number=admission_number,
        enrollment_year=enrollment_year,
        current_semester=1
    )
    db.add(enrollment)
    db.commit()
    
    return {
        "status": "success",
        "message": "Successfully enrolled in program",
        "enrollment_id": enrollment.id
    }

@router.get("/students/{student_id}/program")
def get_student_program(student_id: str, db: Session = Depends(get_db)):
    """Get the program a student is enrolled in"""
    enrollment = db.query(ProgramEnrollment).filter(
        ProgramEnrollment.student_id == student_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="No program enrollment found")
    
    return {
        "status": "success",
        "enrollment": {
            "program_id": enrollment.program_id,
            "program_name": enrollment.program.name,
            "current_semester": enrollment.current_semester,
            "admission_number": enrollment.admission_number,
            "enrollment_year": enrollment.enrollment_year,
            "gpa": enrollment.gpa,
            "status": enrollment.status
        }
    }

@router.get("/students/{student_id}/current-semester")
def get_student_current_semester(student_id: str, db: Session = Depends(get_db)):
    """Get current semester subjects for a student"""
    enrollment = db.query(ProgramEnrollment).filter(
        ProgramEnrollment.student_id == student_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="No program enrollment found")
    
    # Get the current semester
    semester = db.query(Semester).filter(
        Semester.program_id == enrollment.program_id,
        Semester.semester_num == enrollment.current_semester
    ).first()
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    
    subjects = db.query(CollegeCourseSubject).filter(
        CollegeCourseSubject.semester_id == semester.id
    ).all()
    
    return {
        "status": "success",
        "semester": {
            "number": enrollment.current_semester,
            "title": semester.title
        },
        "subjects": [
            {
                "id": s.id,
                "code": s.code,
                "name": s.name,
                "credits": s.credits
            } for s in subjects
        ]
    }

# ─────────────────────────────────────────
# PROGRESS TRACKING
# ─────────────────────────────────────────

@router.get("/students/{student_id}/academic-progress")
def get_academic_progress(student_id: str, db: Session = Depends(get_db)):
    """Get academic progress of a student"""
    enrollment = db.query(ProgramEnrollment).filter(
        ProgramEnrollment.student_id == student_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="No enrollment found")
    
    return {
        "status": "success",
        "progress": {
            "student_id": student_id,
            "program": enrollment.program.name,
            "current_semester": enrollment.current_semester,
            "total_semesters": enrollment.program.total_semesters,
            "gpa": enrollment.gpa,
            "progress_percentage": (enrollment.current_semester / enrollment.program.total_semesters) * 100,
            "status": enrollment.status
        }
    }
