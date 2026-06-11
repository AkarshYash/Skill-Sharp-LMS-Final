from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from auth_utils import get_current_user
import models

router = APIRouter()

class StudyPlanCreate(BaseModel):
    title:       str
    goal:        str
    target_date: str
    weekly_hours: int = 5
    ai_generate: bool = True

@router.get("/my")
def get_my_plans(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plans = db.query(models.StudyPlan).filter(
        models.StudyPlan.student_id == user.id
    ).order_by(models.StudyPlan.created_at.desc()).all()
    
    return [
        {
            "id":          p.id,
            "title":       p.title,
            "goal":        p.goal,
            "target_date": p.target_date,
            "weekly_hours": p.weekly_hours,
            "schedule":    p.schedule or [],
            "milestones":  p.milestones or [],
            "ai_generated": p.ai_generated,
            "created_at":  str(p.created_at),
        }
        for p in plans
    ]

@router.post("/")
async def create_study_plan(
    data: StudyPlanCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    schedule  = []
    milestones = []
    
    if data.ai_generate:
        # Get user's enrolled courses
        enrollments = db.query(models.Enrollment).filter(
            models.Enrollment.student_id == user.id
        ).all()
        courses = []
        for e in enrollments:
            if e.course:
                courses.append({"title": e.course.title, "level": e.course.level})
        
        try:
            from services.ai_service import generate_study_plan
            result = await generate_study_plan(
                goal         = data.goal,
                target_date  = data.target_date,
                weekly_hours = data.weekly_hours,
                courses      = courses,
                student_level = user.student_type or "beginner"
            )
            schedule   = result.get("schedule", [])
            milestones = result.get("milestones", [])
            title      = result.get("title", data.title)
        except Exception as e:
            title = data.title
    else:
        title = data.title
    
    plan = models.StudyPlan(
        student_id   = user.id,
        title        = title,
        goal         = data.goal,
        target_date  = data.target_date,
        weekly_hours = data.weekly_hours,
        schedule     = schedule,
        milestones   = milestones,
        ai_generated = data.ai_generate
    )
    db.add(plan)
    
    # Award XP
    pts = user.points
    if pts:
        pts.xp += 25
    
    db.commit()
    db.refresh(plan)
    
    return {
        "id":          plan.id,
        "title":       plan.title,
        "schedule":    plan.schedule,
        "milestones":  plan.milestones,
        "ai_generated": plan.ai_generated,
    }

@router.put("/{plan_id}/milestone/{milestone_idx}/complete")
def complete_milestone(
    plan_id:       str,
    milestone_idx: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(models.StudyPlan).filter(
        models.StudyPlan.id         == plan_id,
        models.StudyPlan.student_id == user.id
    ).first()
    if not plan:
        raise HTTPException(404, "Plan not found")
    
    milestones = plan.milestones or []
    if 0 <= milestone_idx < len(milestones):
        milestones[milestone_idx]["completed"] = True
        plan.milestones = milestones
        
        # Award XP
        pts = user.points
        if pts:
            pts.xp += 50
        
        db.commit()
    return {"message": "Milestone completed!"}

@router.delete("/{plan_id}")
def delete_plan(
    plan_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(models.StudyPlan).filter(
        models.StudyPlan.id         == plan_id,
        models.StudyPlan.student_id == user.id
    ).first()
    if not plan:
        raise HTTPException(404, "Not found")
    db.delete(plan)
    db.commit()
    return {"message": "Deleted"}
