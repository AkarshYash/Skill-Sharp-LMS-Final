from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from auth_utils import get_current_user, require_role
import models

router = APIRouter()

@router.get("/")
def get_notifications(
    unread_only: bool = False,
    page: int = 1,
    limit: int = 20,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(models.Notification).filter(models.Notification.user_id == user.id)
    if unread_only:
        q = q.filter(models.Notification.is_read == False)
    
    total = q.count()
    notifs = q.order_by(models.Notification.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    
    return {
        "total": total,
        "unread": db.query(models.Notification).filter(
            models.Notification.user_id == user.id,
            models.Notification.is_read == False
        ).count(),
        "notifications": [
            {
                "id":         n.id,
                "title":      n.title,
                "message":    n.message,
                "type":       n.type,
                "data":       n.data,
                "is_read":    n.is_read,
                "created_at": str(n.created_at),
            }
            for n in notifs
        ]
    }

@router.post("/{notification_id}/read")
def mark_read(
    notification_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    n = db.query(models.Notification).filter(
        models.Notification.id      == notification_id,
        models.Notification.user_id == user.id
    ).first()
    if n:
        n.is_read = True
        db.commit()
    return {"message": "Marked as read"}

@router.post("/read-all")
def mark_all_read(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(models.Notification).filter(
        models.Notification.user_id == user.id,
        models.Notification.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "All marked as read"}

@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(models.Notification).filter(
        models.Notification.id      == notification_id,
        models.Notification.user_id == user.id
    ).delete()
    db.commit()
    return {"message": "Deleted"}
