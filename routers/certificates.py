from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import uuid, os

from database import get_db
from auth_utils import get_current_user, require_role
import models

router = APIRouter()

@router.get("/my")
def my_certificates(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    certs = db.query(models.Certificate).filter(
        models.Certificate.student_id == user.id
    ).all()
    
    result = []
    for c in certs:
        course = db.query(models.Course).filter(models.Course.id == c.course_id).first()
        result.append({
            "id":              c.id,
            "course_id":       c.course_id,
            "course_title":    course.title if course else "Unknown",
            "course_thumbnail": course.thumbnail if course else None,
            "certificate_url": c.certificate_url,
            "verify_code":     c.verify_code,
            "issued_at":       str(c.issued_at),
        })
    return result

@router.post("/issue/{course_id}")
def issue_certificate(
    course_id: str,
    user: models.User = Depends(require_role("student")),
    db: Session = Depends(get_db)
):
    # Check completion
    enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == user.id,
        models.Enrollment.course_id  == course_id,
        models.Enrollment.completed  == True
    ).first()
    
    if not enrollment:
        raise HTTPException(400, "Course not completed yet")
    
    # Check if already issued
    existing = db.query(models.Certificate).filter(
        models.Certificate.student_id == user.id,
        models.Certificate.course_id  == course_id
    ).first()
    if existing:
        return {"certificate_id": existing.id, "verify_code": existing.verify_code, "certificate_url": existing.certificate_url}
    
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    
    # Generate PDF certificate
    verify_code = str(uuid.uuid4())[:8].upper()
    cert_filename = f"cert_{user.id}_{course_id}.pdf"
    cert_path = f"static/uploads/certificates/{cert_filename}"
    
    try:
        from services.certificate_service import generate_certificate_pdf
        generate_certificate_pdf(
            student_name = user.name,
            course_title = course.title if course else "Course",
            faculty_name = course.faculty.name if course and course.faculty else "Instructor",
            verify_code  = verify_code,
            output_path  = cert_path
        )
    except Exception as e:
        print(f"Certificate generation error: {e}")
    
    cert = models.Certificate(
        student_id      = user.id,
        course_id       = course_id,
        certificate_url = f"/static/uploads/certificates/{cert_filename}",
        verify_code     = verify_code
    )
    db.add(cert)
    
    # Award XP + badge
    pts = user.points
    if pts:
        pts.xp += 100
    
    # Notification
    notif = models.Notification(
        user_id = user.id,
        title   = "🎓 Certificate Issued!",
        message = f"Congratulations! Your certificate for '{course.title if course else 'the course'}' is ready!",
        type    = "certificate"
    )
    db.add(notif)
    
    db.commit()
    return {"certificate_id": cert.id, "verify_code": verify_code, "certificate_url": cert.certificate_url}

@router.get("/verify/{verify_code}")
def verify_certificate(verify_code: str, db: Session = Depends(get_db)):
    cert = db.query(models.Certificate).filter(
        models.Certificate.verify_code == verify_code
    ).first()
    
    if not cert:
        return {"valid": False, "message": "Certificate not found"}
    
    student = db.query(models.User).filter(models.User.id == cert.student_id).first()
    course  = db.query(models.Course).filter(models.Course.id == cert.course_id).first()
    
    return {
        "valid":         True,
        "student_name":  student.name if student else "Unknown",
        "course_title":  course.title if course else "Unknown",
        "issued_at":     str(cert.issued_at),
        "verify_code":   verify_code
    }
