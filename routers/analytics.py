from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database import get_db
from auth_utils import get_current_user, require_role
import models

router = APIRouter()

@router.get("/student")
def student_analytics(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enrollments = db.query(models.Enrollment).filter(models.Enrollment.student_id == user.id).all()
    completed   = [e for e in enrollments if e.completed]
    pts         = user.points
    
    # Quiz performance
    attempts = db.query(models.QuizAttempt).filter(models.QuizAttempt.student_id == user.id).all()
    avg_score = sum(a.score for a in attempts) / len(attempts) if attempts else 0
    
    # Weekly activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_progress = db.query(models.LectureProgress).filter(
        models.LectureProgress.student_id == user.id,
        models.LectureProgress.updated_at >= week_ago
    ).count()
    
    # Assignment stats
    submissions = db.query(models.AssignmentSubmission).filter(
        models.AssignmentSubmission.student_id == user.id
    ).all()
    graded = [s for s in submissions if s.marks is not None]
    avg_marks = sum(s.marks for s in graded) / len(graded) if graded else 0
    
    # Course progress breakdown
    course_progress = []
    for e in enrollments:
        if e.course:
            course_progress.append({
                "course_id":    e.course_id,
                "course_title": e.course.title,
                "progress":     e.progress,
                "completed":    e.completed,
            })
    
    return {
        "overview": {
            "enrolled_courses":  len(enrollments),
            "completed_courses": len(completed),
            "completion_rate":   int(len(completed) / len(enrollments) * 100) if enrollments else 0,
            "total_xp":          pts.xp if pts else 0,
            "level":             pts.level if pts else 1,
            "streak_days":       pts.streak_days if pts else 0,
        },
        "quiz_stats": {
            "total_attempts": len(attempts),
            "passed":         sum(1 for a in attempts if a.passed),
            "avg_score":      round(avg_score, 1),
        },
        "assignment_stats": {
            "submitted": len(submissions),
            "graded":    len(graded),
            "avg_marks": round(avg_marks, 1),
        },
        "weekly_activity":    recent_progress,
        "course_progress":    course_progress[:10],
    }

@router.get("/faculty")
def faculty_analytics(
    user: models.User = Depends(require_role("faculty", "admin")),
    db: Session = Depends(get_db)
):
    courses = db.query(models.Course).filter(models.Course.faculty_id == user.id).all()
    course_ids = [c.id for c in courses]
    
    total_students = sum(c.total_students for c in courses)
    
    # Enrollments this month
    month_ago = datetime.utcnow() - timedelta(days=30)
    new_enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.course_id.in_(course_ids),
        models.Enrollment.enrolled_at >= month_ago
    ).count()
    
    # Average ratings
    avg_rating = sum(c.rating for c in courses if c.rating) / len(courses) if courses else 0
    
    # Revenue
    payments = db.query(models.Payment).filter(
        models.Payment.course_id.in_(course_ids),
        models.Payment.status == "succeeded"
    ).all()
    total_revenue = sum(p.amount for p in payments)
    
    # Per-course stats
    course_stats = []
    for c in courses:
        enrollments = db.query(models.Enrollment).filter(models.Enrollment.course_id == c.id).count()
        completed   = db.query(models.Enrollment).filter(
            models.Enrollment.course_id == c.id,
            models.Enrollment.completed == True
        ).count()
        course_stats.append({
            "id":           c.id,
            "title":        c.title,
            "students":     c.total_students,
            "enrollments":  enrollments,
            "completed":    completed,
            "rating":       c.rating,
            "is_published": c.is_published,
            "approval_status": c.approval_status,
        })
    
    return {
        "overview": {
            "total_courses":     len(courses),
            "published_courses": sum(1 for c in courses if c.is_published),
            "total_students":    total_students,
            "new_enrollments":   new_enrollments,
            "avg_rating":        round(avg_rating, 2),
            "total_revenue":     total_revenue,
        },
        "course_stats": course_stats,
    }

@router.get("/admin")
def admin_analytics(
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    total_users    = db.query(models.User).count()
    total_students = db.query(models.User).filter(models.User.role == "student").count()
    total_faculty  = db.query(models.User).filter(models.User.role == "faculty").count()
    total_courses  = db.query(models.Course).count()
    published      = db.query(models.Course).filter(models.Course.is_published == True).count()
    pending        = db.query(models.Course).filter(models.Course.approval_status == "pending").count()
    total_enroll   = db.query(models.Enrollment).count()
    total_certs    = db.query(models.Certificate).count()
    
    # Revenue
    payments = db.query(models.Payment).filter(models.Payment.status == "succeeded").all()
    total_revenue = sum(p.amount for p in payments)
    
    # New users this month
    month_ago = datetime.utcnow() - timedelta(days=30)
    new_users = db.query(models.User).filter(models.User.created_at >= month_ago).count()
    
    # Recent enrollments
    recent_enroll = db.query(models.Enrollment).filter(
        models.Enrollment.enrolled_at >= month_ago
    ).count()
    
    # Top courses
    top_courses = db.query(models.Course).filter(
        models.Course.is_published == True
    ).order_by(models.Course.total_students.desc()).limit(5).all()
    
    return {
        "overview": {
            "total_users":     total_users,
            "total_students":  total_students,
            "total_faculty":   total_faculty,
            "total_courses":   total_courses,
            "published_courses": published,
            "pending_approval":  pending,
            "total_enrollments": total_enroll,
            "total_certificates": total_certs,
            "total_revenue":   total_revenue,
            "new_users_month": new_users,
            "new_enrollments_month": recent_enroll,
        },
        "top_courses": [
            {"id": c.id, "title": c.title, "students": c.total_students, "rating": c.rating}
            for c in top_courses
        ],
    }

@router.get("/leaderboard")
def get_leaderboard(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    top_users = db.query(models.UserPoints).order_by(
        models.UserPoints.xp.desc()
    ).limit(limit).all()
    
    result = []
    for i, up in enumerate(top_users):
        user = db.query(models.User).filter(models.User.id == up.user_id).first()
        if not user:
            continue
        badges = db.query(models.UserBadge).filter(models.UserBadge.user_id == up.user_id).count()
        completed = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == up.user_id,
            models.Enrollment.completed  == True
        ).count()
        result.append({
            "rank":             i + 1,
            "user_id":          up.user_id,
            "name":             user.name,
            "avatar":           user.avatar,
            "role":             user.role,
            "xp":               up.xp,
            "level":            up.level,
            "streak_days":      up.streak_days,
            "badges":           badges,
            "courses_completed": completed,
        })
    return result
