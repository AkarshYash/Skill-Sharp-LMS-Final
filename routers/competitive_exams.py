"""
Competitive Exams Module - UPSC, JEE, NEET, CAT, etc.
Skill Sharp 365 Innovations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import (
    CompetitiveExam, ExamStudyMaterial, MockTest, MockTestQuestion,
    MockTestAttempt, ExamEnrollment
)
from pydantic import BaseModel
from datetime import datetime

class MockTestAttemptCreate(BaseModel):
    student_id: str
    answers: dict  # {question_id: answer}

router = APIRouter()

# ─────────────────────────────────────────
# EXAM CATALOG
# ─────────────────────────────────────────

@router.get("/exams")
def get_all_exams(db: Session = Depends(get_db)):
    """Get all available competitive exams"""
    exams = db.query(CompetitiveExam).all()
    return {
        "status": "success",
        "exams": [
            {
                "id": e.id,
                "name": e.exam_name,
                "type": e.exam_type,
                "difficulty": e.difficulty
            } for e in exams
        ]
    }

@router.get("/exams/{exam_id}")
def get_exam_details(exam_id: str, db: Session = Depends(get_db)):
    """Get detailed info about an exam"""
    exam = db.query(CompetitiveExam).filter(
        CompetitiveExam.id == exam_id
    ).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Count study materials and mock tests
    materials_count = db.query(ExamStudyMaterial).filter(
        ExamStudyMaterial.exam_id == exam_id
    ).count()
    tests_count = db.query(MockTest).filter(
        MockTest.exam_id == exam_id
    ).count()
    
    return {
        "status": "success",
        "exam": {
            "id": exam.id,
            "name": exam.exam_name,
            "type": exam.exam_type,
            "difficulty": exam.difficulty,
            "description": exam.description,
            "resources": {
                "study_materials": materials_count,
                "mock_tests": tests_count
            }
        }
    }

# ─────────────────────────────────────────
# STUDY MATERIALS
# ─────────────────────────────────────────

@router.get("/exams/{exam_id}/materials")
def get_exam_materials(
    exam_id: str,
    material_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get study materials for an exam"""
    query = db.query(ExamStudyMaterial).filter(
        ExamStudyMaterial.exam_id == exam_id
    )
    
    if material_type:
        query = query.filter(ExamStudyMaterial.material_type == material_type)
    
    materials = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "status": "success",
        "total": total,
        "materials": [
            {
                "id": m.id,
                "title": m.title,
                "topic": m.topic,
                "type": m.material_type,
                "url": m.url,
                "views": m.views
            } for m in materials
        ]
    }

@router.get("/materials/{material_id}/view")
def view_material(material_id: str, db: Session = Depends(get_db)):
    """View/download a study material"""
    material = db.query(ExamStudyMaterial).filter(
        ExamStudyMaterial.id == material_id
    ).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Increment view count
    material.views += 1
    db.commit()
    
    return {
        "status": "success",
        "material": {
            "title": material.title,
            "topic": material.topic,
            "type": material.material_type,
            "url": material.url,
            "views": material.views
        }
    }

# ─────────────────────────────────────────
# MOCK TESTS
# ─────────────────────────────────────────

@router.get("/exams/{exam_id}/mock-tests")
def get_exam_mock_tests(exam_id: str, db: Session = Depends(get_db)):
    """Get all mock tests for an exam"""
    mock_tests = db.query(MockTest).filter(
        MockTest.exam_id == exam_id
    ).all()
    
    return {
        "status": "success",
        "tests": [
            {
                "id": t.id,
                "title": t.title,
                "total_questions": t.total_questions,
                "total_marks": t.total_marks,
                "duration_minutes": t.duration,
                "negative_marking": t.negative_marking
            } for t in mock_tests
        ]
    }

@router.get("/mock-tests/{test_id}")
def get_mock_test_details(test_id: str, db: Session = Depends(get_db)):
    """Get full mock test with questions"""
    mock_test = db.query(MockTest).filter(MockTest.id == test_id).first()
    if not mock_test:
        raise HTTPException(status_code=404, detail="Mock test not found")
    
    questions = db.query(MockTestQuestion).filter(
        MockTestQuestion.mock_test_id == test_id
    ).order_by(MockTestQuestion.order_index).all()
    
    return {
        "status": "success",
        "test": {
            "id": mock_test.id,
            "title": mock_test.title,
            "duration": mock_test.duration,
            "total_marks": mock_test.total_marks,
            "total_questions": mock_test.total_questions,
            "negative_marking": mock_test.negative_marking,
            "description": mock_test.description
        },
        "questions": [
            {
                "id": q.id,
                "question": q.question,
                "options": q.options,
                "marks": q.marks
            } for q in questions
        ]
    }

@router.post("/mock-tests/{test_id}/start")
def start_mock_test(test_id: str, student_id: str):
    """Start attempting a mock test"""
    return {
        "status": "success",
        "message": "Mock test started",
        "test_id": test_id,
        "student_id": student_id,
        "start_time": datetime.now()
    }

@router.post("/mock-tests/{test_id}/submit")
def submit_mock_test(
    test_id: str,
    attempt_data: MockTestAttemptCreate,
    time_taken: int,  # seconds
    db: Session = Depends(get_db)
):
    """Submit mock test attempt and get AI analysis"""
    mock_test = db.query(MockTest).filter(MockTest.id == test_id).first()
    if not mock_test:
        raise HTTPException(status_code=404, detail="Mock test not found")
    
    # Get questions and calculate score
    questions = db.query(MockTestQuestion).filter(
        MockTestQuestion.mock_test_id == test_id
    ).all()
    
    score = 0
    correct_answers = 0
    for q in questions:
        if attempt_data.answers.get(q.id) == q.correct_answer:
            score += q.marks
            correct_answers += 1
    
    percentage = (score / mock_test.total_marks * 100) if mock_test.total_marks > 0 else 0
    
    # Store attempt
    attempt = MockTestAttempt(
        mock_test_id=test_id,
        student_id=attempt_data.student_id,
        score=score,
        percentage=percentage,
        time_taken=time_taken
    )
    db.add(attempt)
    db.commit()
    
    # Generate AI analysis (placeholder)
    ai_analysis = f"You scored {score}/{mock_test.total_marks} ({percentage:.1f}%). Attempted {len(attempt_data.answers)}/{mock_test.total_questions} questions. Correct answers: {correct_answers}."
    
    return {
        "status": "success",
        "message": "Mock test submitted",
        "result": {
            "attempt_id": attempt.id,
            "score": score,
            "max_score": mock_test.total_marks,
            "percentage": round(percentage, 2),
            "correct_answers": correct_answers,
            "total_questions": mock_test.total_questions,
            "time_taken_minutes": round(time_taken / 60, 2),
            "ai_analysis": ai_analysis
        }
    }

@router.get("/mock-tests/{test_id}/results/{attempt_id}")
def get_mock_test_results(test_id: str, attempt_id: str, db: Session = Depends(get_db)):
    """Get detailed results of a mock test attempt"""
    attempt = db.query(MockTestAttempt).filter(
        MockTestAttempt.id == attempt_id,
        MockTestAttempt.mock_test_id == test_id
    ).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    # Get questions with student answers
    questions = db.query(MockTestQuestion).filter(
        MockTestQuestion.mock_test_id == test_id
    ).all()
    
    return {
        "status": "success",
        "result": {
            "score": attempt.score,
            "percentage": attempt.percentage,
            "time_taken": attempt.time_taken,
            "attempted_at": attempt.attempted_at
        }
    }

# ─────────────────────────────────────────
# ENROLLMENT & PROGRESS
# ─────────────────────────────────────────

@router.post("/enroll")
def enroll_exam_prep(
    student_id: str,
    exam_id: str,
    db: Session = Depends(get_db)
):
    """Enroll a student in exam preparation"""
    exam = db.query(CompetitiveExam).filter(
        CompetitiveExam.id == exam_id
    ).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Check duplicate enrollment
    existing = db.query(ExamEnrollment).filter(
        ExamEnrollment.student_id == student_id,
        ExamEnrollment.exam_id == exam_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled")
    
    enrollment = ExamEnrollment(
        student_id=student_id,
        exam_id=exam_id
    )
    db.add(enrollment)
    db.commit()
    
    return {
        "status": "success",
        "message": f"Enrolled in {exam.exam_name} preparation"
    }

@router.get("/students/{student_id}/enrolled-exams")
def get_student_enrolled_exams(student_id: str, db: Session = Depends(get_db)):
    """Get exams a student is enrolled in"""
    enrollments = db.query(ExamEnrollment).filter(
        ExamEnrollment.student_id == student_id
    ).all()
    
    return {
        "status": "success",
        "exams": [
            {
                "exam_id": e.exam_id,
                "exam_name": e.exam.exam_name,
                "exam_type": e.exam.exam_type,
                "enrolled_at": e.enrolled_at
            } for e in enrollments
        ]
    }

# ─────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────

@router.get("/students/{student_id}/exam/{exam_id}/progress")
def get_exam_progress(
    student_id: str,
    exam_id: str,
    db: Session = Depends(get_db)
):
    """Get exam preparation progress"""
    # Get all mock test attempts
    attempts = db.query(MockTestAttempt).join(
        MockTest, MockTest.id == MockTestAttempt.mock_test_id
    ).filter(
        MockTestAttempt.student_id == student_id,
        MockTest.exam_id == exam_id
    ).all()
    
    avg_score = sum([a.percentage for a in attempts]) / len(attempts) if attempts else 0
    
    return {
        "status": "success",
        "progress": {
            "total_tests_attempted": len(attempts),
            "average_score": round(avg_score, 2),
            "best_score": max([a.percentage for a in attempts]) if attempts else 0,
            "test_performance": [
                {
                    "test_id": a.mock_test_id,
                    "score": a.percentage,
                    "attempted_at": a.attempted_at
                } for a in sorted(attempts, key=lambda x: x.attempted_at)
            ]
        }
    }
