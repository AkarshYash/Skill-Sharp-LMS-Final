"""
Professional Courses Marketplace - Coursera/Udemy style courses
Skill Sharp 365 Innovations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import ProfessionalCourse, CourseSection, CourseLesson, ProfessionalEnrollment, CourseReview
from pydantic import BaseModel
from datetime import datetime

class CourseCreate(BaseModel):
    title: str
    description: str
    category: str
    subcategory: str
    difficulty: str
    price: float = 0
    promo_video: Optional[str] = None

router = APIRouter()

# ─────────────────────────────────────────
# COURSE BROWSING
# ─────────────────────────────────────────

@router.get("/courses")
def get_professional_courses(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    sort_by: str = "popular",
    db: Session = Depends(get_db)
):
    """Get professional courses with filters"""
    query = db.query(ProfessionalCourse).filter(
        ProfessionalCourse.is_published == True
    )
    
    if category:
        query = query.filter(ProfessionalCourse.category == category)
    if difficulty:
        query = query.filter(ProfessionalCourse.difficulty == difficulty)
    
    # Sort options
    if sort_by == "popular":
        query = query.order_by(ProfessionalCourse.total_students.desc())
    elif sort_by == "rating":
        query = query.order_by(ProfessionalCourse.rating.desc())
    elif sort_by == "newest":
        query = query.order_by(ProfessionalCourse.created_at.desc())
    
    total = query.count()
    courses = query.offset(skip).limit(limit).all()
    
    return {
        "status": "success",
        "total": total,
        "courses": [
            {
                "id": c.id,
                "title": c.title,
                "instructor": c.instructor_id,
                "category": c.category,
                "difficulty": c.difficulty,
                "price": c.price,
                "rating": c.rating,
                "total_students": c.total_students,
                "total_duration": c.total_duration,
                "thumbnail": c.thumbnail
            } for c in courses
        ]
    }

@router.get("/courses/{course_id}")
def get_course_details(course_id: str, db: Session = Depends(get_db)):
    """Get detailed course information"""
    course = db.query(ProfessionalCourse).filter(
        ProfessionalCourse.id == course_id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    sections = db.query(CourseSection).filter(
        CourseSection.course_id == course_id
    ).order_by(CourseSection.order_index).all()
    
    reviews = db.query(CourseReview).filter(
        CourseReview.course_id == course_id
    ).all()
    
    return {
        "status": "success",
        "course": {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "subcategory": course.subcategory,
            "instructor_id": course.instructor_id,
            "price": course.price,
            "currency": course.currency,
            "difficulty": course.difficulty,
            "rating": course.rating,
            "total_rating_count": course.total_rating_count,
            "total_students": course.total_students,
            "total_duration": course.total_duration,
            "thumbnail": course.thumbnail,
            "promo_video": course.promo_video
        },
        "sections": [
            {
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "order": s.order_index,
                "lessons_count": len(s.lessons) if s.lessons else 0
            } for s in sections
        ],
        "reviews": {
            "total": len(reviews),
            "average_rating": course.rating,
            "reviews": [
                {
                    "rating": r.rating,
                    "review_text": r.review_text,
                    "helpful_count": r.helpful_count,
                    "created_at": r.created_at
                } for r in reviews[:5]  # Show top 5 reviews
            ]
        }
    }

# ─────────────────────────────────────────
# COURSE CONTENT
# ─────────────────────────────────────────

@router.get("/courses/{course_id}/sections")
def get_course_sections(course_id: str, db: Session = Depends(get_db)):
    """Get all sections in a course"""
    sections = db.query(CourseSection).filter(
        CourseSection.course_id == course_id
    ).order_by(CourseSection.order_index).all()
    
    return {
        "status": "success",
        "sections": [
            {
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "order": s.order_index,
                "lessons": [
                    {
                        "id": l.id,
                        "title": l.title,
                        "video_url": l.video_url,
                        "duration": l.duration
                    } for l in s.lessons
                ]
            } for s in sections
        ]
    }

@router.get("/sections/{section_id}/lessons")
def get_section_lessons(section_id: str, db: Session = Depends(get_db)):
    """Get all lessons in a section"""
    lessons = db.query(CourseLesson).filter(
        CourseLesson.section_id == section_id
    ).order_by(CourseLesson.order_index).all()
    
    return {
        "status": "success",
        "lessons": [
            {
                "id": l.id,
                "title": l.title,
                "description": l.description,
                "video_url": l.video_url,
                "duration": l.duration,
                "resources": l.resources
            } for l in lessons
        ]
    }

@router.get("/lessons/{lesson_id}")
def get_lesson_details(lesson_id: str, db: Session = Depends(get_db)):
    """Get detailed lesson information"""
    lesson = db.query(CourseLesson).filter(
        CourseLesson.id == lesson_id
    ).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return {
        "status": "success",
        "lesson": {
            "id": lesson.id,
            "title": lesson.title,
            "description": lesson.description,
            "video_url": lesson.video_url,
            "duration": lesson.duration,
            "resources": lesson.resources
        }
    }

# ─────────────────────────────────────────
# ENROLLMENT & PROGRESS
# ─────────────────────────────────────────

@router.post("/enroll")
def enroll_course(
    student_id: str,
    course_id: str,
    db: Session = Depends(get_db)
):
    """Enroll a student in a professional course"""
    course = db.query(ProfessionalCourse).filter(
        ProfessionalCourse.id == course_id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check duplicate enrollment
    existing = db.query(ProfessionalEnrollment).filter(
        ProfessionalEnrollment.student_id == student_id,
        ProfessionalEnrollment.course_id == course_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled")
    
    enrollment = ProfessionalEnrollment(
        student_id=student_id,
        course_id=course_id,
        enrolled_at=datetime.now()
    )
    
    # Update course stats
    course.total_students += 1
    
    db.add(enrollment)
    db.commit()
    
    return {
        "status": "success",
        "message": "Enrolled in course",
        "enrollment_id": enrollment.id
    }

@router.get("/students/{student_id}/enrolled-courses")
def get_student_enrolled_courses(student_id: str, db: Session = Depends(get_db)):
    """Get all courses a student is enrolled in"""
    enrollments = db.query(ProfessionalEnrollment).filter(
        ProfessionalEnrollment.student_id == student_id
    ).all()
    
    return {
        "status": "success",
        "courses": [
            {
                "enrollment_id": e.id,
                "course_id": e.course_id,
                "title": e.course.title,
                "progress": e.progress,
                "completed": e.completed,
                "certificate_issued": e.certificate_issued,
                "enrolled_at": e.enrolled_at
            } for e in enrollments
        ]
    }

@router.post("/enrollments/{enrollment_id}/update-progress")
def update_course_progress(
    enrollment_id: str,
    progress_percentage: int,
    db: Session = Depends(get_db)
):
    """Update course progress"""
    enrollment = db.query(ProfessionalEnrollment).filter(
        ProfessionalEnrollment.id == enrollment_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    enrollment.progress = progress_percentage
    if progress_percentage >= 100:
        enrollment.completed = True
        enrollment.completed_at = datetime.now()
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Progress updated",
        "progress": enrollment.progress,
        "completed": enrollment.completed
    }

# ─────────────────────────────────────────
# REVIEWS & RATINGS
# ─────────────────────────────────────────

@router.post("/courses/{course_id}/review")
def add_course_review(
    course_id: str,
    student_id: str,
    rating: int,
    review_text: str,
    db: Session = Depends(get_db)
):
    """Add review to a course"""
    course = db.query(ProfessionalCourse).filter(
        ProfessionalCourse.id == course_id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    
    # Check if already reviewed
    existing = db.query(CourseReview).filter(
        CourseReview.course_id == course_id,
        CourseReview.student_id == student_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already reviewed this course")
    
    review = CourseReview(
        course_id=course_id,
        student_id=student_id,
        rating=rating,
        review_text=review_text
    )
    db.add(review)
    
    # Update course rating
    all_reviews = db.query(CourseReview).filter(
        CourseReview.course_id == course_id
    ).all()
    total_rating = sum([r.rating for r in all_reviews]) + rating
    avg_rating = total_rating / (len(all_reviews) + 1)
    
    course.rating = round(avg_rating, 1)
    course.total_rating_count = len(all_reviews) + 1
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Review added",
        "course_new_rating": course.rating
    }

@router.get("/courses/{course_id}/reviews")
def get_course_reviews(
    course_id: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all reviews for a course"""
    reviews = db.query(CourseReview).filter(
        CourseReview.course_id == course_id
    ).order_by(CourseReview.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "status": "success",
        "reviews": [
            {
                "rating": r.rating,
                "review_text": r.review_text,
                "helpful_count": r.helpful_count,
                "created_at": r.created_at
            } for r in reviews
        ]
    }

# ─────────────────────────────────────────
# CATEGORIES & SEARCH
# ─────────────────────────────────────────

@router.get("/categories")
def get_course_categories(db: Session = Depends(get_db)):
    """Get all course categories"""
    categories = db.query(ProfessionalCourse.category).distinct().all()
    return {
        "status": "success",
        "categories": [c[0] for c in categories if c[0]]
    }

@router.get("/search")
def search_courses(
    query: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Search for courses"""
    courses = db.query(ProfessionalCourse).filter(
        (ProfessionalCourse.title.ilike(f"%{query}%")) |
        (ProfessionalCourse.description.ilike(f"%{query}%")) |
        (ProfessionalCourse.category.ilike(f"%{query}%"))
    ).offset(skip).limit(limit).all()
    
    return {
        "status": "success",
        "total": len(courses),
        "courses": [
            {
                "id": c.id,
                "title": c.title,
                "category": c.category,
                "rating": c.rating,
                "price": c.price
            } for c in courses
        ]
    }
