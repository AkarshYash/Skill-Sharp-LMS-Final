from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from auth_utils import get_current_user, require_role
import models

router = APIRouter()

class InternshipCreate(BaseModel):
    title:       str
    company:     str
    description: str
    location:    str = "Remote"
    type:        str = "internship"
    stipend:     str = "Unpaid"
    skills:      List[str] = []
    apply_url:   str
    deadline:    str

@router.get("/")
def list_opportunities(
    type:    Optional[str] = None,
    search:  Optional[str] = None,
    page:    int = 1,
    limit:   int = 12,
    db: Session = Depends(get_db)
):
    q = db.query(models.Internship).filter(models.Internship.is_active == True)
    if type:
        q = q.filter(models.Internship.type == type)
    if search:
        q = q.filter(
            models.Internship.title.ilike(f"%{search}%") |
            models.Internship.company.ilike(f"%{search}%")
        )
    
    total = q.count()
    items = q.order_by(models.Internship.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    
    return {
        "total": total,
        "items": [
            {
                "id":          i.id,
                "title":       i.title,
                "company":     i.company,
                "description": i.description,
                "location":    i.location,
                "type":        i.type,
                "stipend":     i.stipend,
                "skills":      i.skills or [],
                "apply_url":   i.apply_url,
                "deadline":    i.deadline,
                "created_at":  str(i.created_at),
            }
            for i in items
        ]
    }

@router.post("/")
def create_opportunity(
    data: InternshipCreate,
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    item = models.Internship(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "title": item.title}

@router.delete("/{item_id}")
def delete_opportunity(
    item_id: str,
    admin: models.User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    item = db.query(models.Internship).filter(models.Internship.id == item_id).first()
    if not item:
        raise HTTPException(404, "Not found")
    item.is_active = False
    db.commit()
    return {"message": "Deactivated"}

@router.get("/ai-recommendations")
async def get_career_ai_recommendations(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI-powered career path recommendations"""
    # Gather user data
    completed = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == user.id,
        models.Enrollment.completed  == True
    ).all()
    
    course_titles = []
    for e in completed:
        if e.course:
            course_titles.append(e.course.title)
    
    skills = []
    if user.expertise:
        skills = [s.strip() for s in user.expertise.split(",")]
    
    try:
        from services.ai_service import get_career_recommendations
        recommendations = await get_career_recommendations(
            skills  = skills,
            courses = course_titles,
            goal    = user.bio or ""
        )
        return recommendations
    except Exception as e:
        return {
            "recommended_paths": [
                {"title": "Full Stack Developer", "match": 85, "description": "Build web applications end-to-end", "next_steps": ["Complete web development courses", "Build portfolio projects"]},
                {"title": "Data Scientist",       "match": 70, "description": "Analyze data and build ML models",  "next_steps": ["Learn Python and ML", "Work with real datasets"]},
            ],
            "skill_gaps":           ["Machine Learning", "Cloud Computing"],
            "recommended_courses":  ["Advanced Python", "Data Science with ML"],
            "market_insight":       "Tech roles are in high demand globally."
        }
