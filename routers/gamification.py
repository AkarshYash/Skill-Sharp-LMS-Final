from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth_utils import get_current_user, require_role
import models

router = APIRouter()

@router.get("/my-points")
def get_my_points(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pts = user.points
    if not pts:
        pts = models.UserPoints(user_id=user.id)
        db.add(pts)
        db.commit()
    
    badges = db.query(models.UserBadge).filter(models.UserBadge.user_id == user.id).all()
    badge_details = []
    for ub in badges:
        b = db.query(models.Badge).filter(models.Badge.id == ub.badge_id).first()
        if b:
            badge_details.append({
                "id": b.id, "name": b.name, "description": b.description,
                "icon": b.icon, "color": b.color, "earned_at": str(ub.earned_at)
            })
    
    # Level thresholds
    level = 1
    xp = pts.xp
    for lvl in range(1, 100):
        if xp < lvl * 100:
            level = lvl
            break
    
    pts.level = level
    db.commit()
    
    return {
        "xp":          pts.xp,
        "level":       pts.level,
        "streak_days": pts.streak_days,
        "next_level_xp": pts.level * 100,
        "badges":      badge_details,
    }

@router.get("/badges")
def get_all_badges(db: Session = Depends(get_db)):
    badges = db.query(models.Badge).all()
    return [
        {"id": b.id, "name": b.name, "description": b.description, "icon": b.icon, "color": b.color}
        for b in badges
    ]

@router.post("/check-badges")
def check_and_award_badges(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pts = user.points
    if not pts:
        return {"badges_earned": []}
    
    all_badges   = db.query(models.Badge).all()
    user_badges  = {ub.badge_id for ub in db.query(models.UserBadge).filter(models.UserBadge.user_id == user.id).all()}
    earned       = []
    
    completed_courses = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == user.id,
        models.Enrollment.completed  == True
    ).count()
    
    for b in all_badges:
        if b.id in user_badges:
            continue
        
        award = False
        if b.condition_type == "xp_earned" and pts.xp >= b.condition_value:
            award = True
        elif b.condition_type == "courses_completed" and completed_courses >= b.condition_value:
            award = True
        elif b.condition_type == "streak" and pts.streak_days >= b.condition_value:
            award = True
        
        if award:
            ub = models.UserBadge(user_id=user.id, badge_id=b.id)
            db.add(ub)
            earned.append({"name": b.name, "icon": b.icon})
    
    db.commit()
    return {"badges_earned": earned}
