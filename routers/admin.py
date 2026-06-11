from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
from auth_utils import require_role, get_current_user
import models

router = APIRouter()

class SeedBadges(BaseModel):
    confirm: bool = True

@router.get("/dashboard")
def admin_dashboard(
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    total_users    = db.query(models.User).count()
    total_courses  = db.query(models.Course).count()
    total_enroll   = db.query(models.Enrollment).count()
    pending        = db.query(models.Course).filter(models.Course.approval_status == "pending").count()
    
    recent_users = db.query(models.User).order_by(models.User.created_at.desc()).limit(5).all()
    
    return {
        "stats": {
            "total_users":    total_users,
            "total_courses":  total_courses,
            "total_enrollments": total_enroll,
            "pending_approvals": pending,
        },
        "recent_users": [
            {"id": u.id, "name": u.name, "email": u.email, "role": u.role, "created_at": str(u.created_at)}
            for u in recent_users
        ]
    }

@router.post("/seed-badges")
def seed_badges(
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Seed default badges"""
    default_badges = [
        {"name": "First Step",       "description": "Enrolled in first course", "icon": "🎯", "condition_type": "courses_completed", "condition_value": 1,   "color": "#6366f1"},
        {"name": "Scholar",          "description": "Completed 5 courses",       "icon": "📚", "condition_type": "courses_completed", "condition_value": 5,   "color": "#8b5cf6"},
        {"name": "Expert",           "description": "Completed 10 courses",      "icon": "🏆", "condition_type": "courses_completed", "condition_value": 10,  "color": "#f59e0b"},
        {"name": "Master",           "description": "Completed 25 courses",      "icon": "👑", "condition_type": "courses_completed", "condition_value": 25,  "color": "#ef4444"},
        {"name": "XP Hunter",        "description": "Earned 100 XP",            "icon": "⚡", "condition_type": "xp_earned",         "condition_value": 100, "color": "#10b981"},
        {"name": "Power Learner",    "description": "Earned 500 XP",            "icon": "🚀", "condition_type": "xp_earned",         "condition_value": 500, "color": "#3b82f6"},
        {"name": "Legend",           "description": "Earned 1000 XP",           "icon": "🌟", "condition_type": "xp_earned",         "condition_value": 1000,"color": "#f97316"},
        {"name": "Week Warrior",     "description": "7-day streak",             "icon": "🔥", "condition_type": "streak",            "condition_value": 7,   "color": "#ef4444"},
        {"name": "Month Champion",   "description": "30-day streak",            "icon": "💎", "condition_type": "streak",            "condition_value": 30,  "color": "#06b6d4"},
    ]
    
    added = 0
    for badge_data in default_badges:
        exists = db.query(models.Badge).filter(models.Badge.name == badge_data["name"]).first()
        if not exists:
            badge = models.Badge(**badge_data)
            db.add(badge)
            added += 1
    
    db.commit()
    return {"message": f"Seeded {added} badges"}

@router.post("/seed-demo-courses")
def seed_demo_courses(
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """Seed demo courses for showcase"""
    demo_courses = [
        {
            "title": "Python for AI & Machine Learning",
            "description": "Master Python programming and build AI applications. Covers NumPy, Pandas, Scikit-learn, TensorFlow, and PyTorch.",
            "short_desc": "Complete Python ML course from beginner to expert",
            "category": "Artificial Intelligence",
            "level": "intermediate",
            "price": 0,
            "tags": ["python", "machine-learning", "AI", "deep-learning"],
            "what_you_learn": ["Python fundamentals", "Data manipulation with Pandas", "ML algorithms", "Deep learning with TensorFlow"],
            "requirements": ["Basic programming knowledge", "Mathematics basics"],
            "approval_status": "approved",
            "is_published": True,
            "rating": 4.8,
            "total_students": 1245,
            "duration_hours": 40
        },
        {
            "title": "LangChain & RAG: Building LLM Applications",
            "description": "Build production-ready LLM applications using LangChain, OpenAI, and vector databases. Includes RAG pipelines and agent architectures.",
            "short_desc": "Build LLM apps with LangChain and RAG",
            "category": "Artificial Intelligence",
            "level": "advanced",
            "price": 0,
            "tags": ["langchain", "RAG", "LLM", "openai", "chromadb"],
            "what_you_learn": ["LangChain fundamentals", "RAG pipeline design", "Vector databases", "AI agents"],
            "requirements": ["Python knowledge", "Basic ML understanding"],
            "approval_status": "approved",
            "is_published": True,
            "rating": 4.9,
            "total_students": 892,
            "duration_hours": 30
        },
        {
            "title": "Full Stack Web Development",
            "description": "Complete web development from HTML/CSS to React, Node.js, and databases. Build 5 real-world projects.",
            "short_desc": "Full stack web dev with React & Node.js",
            "category": "Web Development",
            "level": "beginner",
            "price": 0,
            "tags": ["javascript", "react", "nodejs", "fullstack"],
            "what_you_learn": ["HTML/CSS/JavaScript", "React framework", "REST APIs", "Database design"],
            "requirements": ["No prior experience needed"],
            "approval_status": "approved",
            "is_published": True,
            "rating": 4.7,
            "total_students": 2341,
            "duration_hours": 60
        },
        {
            "title": "Data Science with Python",
            "description": "Learn data analysis, visualization, and statistical modeling. Work with real datasets from Kaggle.",
            "short_desc": "Data science from scratch to professional",
            "category": "Data Science",
            "level": "intermediate",
            "price": 0,
            "tags": ["python", "data-science", "pandas", "visualization"],
            "what_you_learn": ["Data wrangling", "Statistical analysis", "Data visualization", "Predictive modeling"],
            "requirements": ["Basic Python knowledge"],
            "approval_status": "approved",
            "is_published": True,
            "rating": 4.6,
            "total_students": 1876,
            "duration_hours": 45
        },
        {
            "title": "Cybersecurity & Ethical Hacking",
            "description": "Learn ethical hacking, penetration testing, and cybersecurity fundamentals. Get certified ready.",
            "short_desc": "Ethical hacking and cybersecurity fundamentals",
            "category": "Cybersecurity",
            "level": "intermediate",
            "price": 0,
            "tags": ["cybersecurity", "ethical-hacking", "networking", "security"],
            "what_you_learn": ["Network security", "Penetration testing", "Web app security", "Incident response"],
            "requirements": ["Basic networking knowledge"],
            "approval_status": "approved",
            "is_published": True,
            "rating": 4.8,
            "total_students": 934,
            "duration_hours": 50
        },
        {
            "title": "Cloud Computing with AWS",
            "description": "Master AWS services: EC2, S3, Lambda, RDS, and more. Prepare for AWS certification.",
            "short_desc": "AWS cloud computing from zero to certified",
            "category": "Cloud Computing",
            "level": "intermediate",
            "price": 0,
            "tags": ["AWS", "cloud", "devops", "infrastructure"],
            "what_you_learn": ["AWS core services", "Serverless architecture", "Cloud security", "Cost optimization"],
            "requirements": ["Basic IT knowledge"],
            "approval_status": "approved",
            "is_published": True,
            "rating": 4.7,
            "total_students": 1123,
            "duration_hours": 35
        },
    ]
    
    added = 0
    for course_data in demo_courses:
        exists = db.query(models.Course).filter(models.Course.title == course_data["title"]).first()
        if not exists:
            course = models.Course(faculty_id=admin.id, **course_data)
            db.add(course)
            added += 1
    
    db.commit()
    return {"message": f"Added {added} demo courses"}

@router.get("/users")
def list_all_users(
    role:   Optional[str] = None,
    search: Optional[str] = None,
    page:   int = 1,
    limit:  int = 20,
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from typing import Optional
    q = db.query(models.User)
    if role:
        q = q.filter(models.User.role == role)
    if search:
        q = q.filter(models.User.name.ilike(f"%{search}%") | models.User.email.ilike(f"%{search}%"))
    
    total = q.count()
    users = q.order_by(models.User.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    
    return {
        "total": total,
        "users": [
            {
                "id":         u.id,
                "name":       u.name,
                "email":      u.email,
                "role":       u.role,
                "avatar":     u.avatar,
                "is_active":  u.is_active,
                "is_verified": u.is_verified,
                "created_at": str(u.created_at),
                "last_login": str(u.last_login) if u.last_login else None,
            }
            for u in users
        ]
    }

@router.post("/create-admin")
def create_admin_user(
    name:     str,
    email:    str,
    password: str,
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from auth_utils import hash_password
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(400, "Email already exists")
    
    user = models.User(
        name       = name,
        email      = email,
        password   = hash_password(password),
        role       = "admin",
        is_verified = True
    )
    db.add(user)
    
    pts = models.UserPoints(user_id=user.id)
    db.add(pts)
    db.commit()
    return {"id": user.id, "name": user.name, "email": user.email}

@router.get("/system-stats")
def system_stats(
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    from datetime import timedelta
    month_ago = datetime.utcnow() - timedelta(days=30)
    week_ago  = datetime.utcnow() - timedelta(days=7)
    
    return {
        "database": {
            "total_users":        db.query(models.User).count(),
            "total_courses":      db.query(models.Course).count(),
            "total_enrollments":  db.query(models.Enrollment).count(),
            "total_certificates": db.query(models.Certificate).count(),
            "total_messages":     db.query(models.Message).count(),
            "total_quiz_attempts": db.query(models.QuizAttempt).count(),
            "total_ai_sessions":  db.query(models.AITutorSession).count(),
        },
        "activity": {
            "new_users_this_month":  db.query(models.User).filter(models.User.created_at >= month_ago).count(),
            "new_users_this_week":   db.query(models.User).filter(models.User.created_at >= week_ago).count(),
            "enrollments_this_month": db.query(models.Enrollment).filter(models.Enrollment.enrolled_at >= month_ago).count(),
        }
    }
