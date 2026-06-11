from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import uuid

from database import get_db
from auth_utils import get_current_user, require_role
import models

router = APIRouter()

# ─── Messages ────────────────────────────────────

class SendMessage(BaseModel):
    receiver_id: Optional[str] = None
    course_id:   Optional[str] = None
    content:     str
    type:        str = "text"

@router.get("/conversations")
def get_conversations(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's unique conversations (DMs)"""
    sent = db.query(models.Message).filter(
        models.Message.sender_id   == user.id,
        models.Message.receiver_id != None
    ).all()
    received = db.query(models.Message).filter(
        models.Message.receiver_id == user.id
    ).all()
    
    partners = set()
    for m in sent:
        partners.add(m.receiver_id)
    for m in received:
        partners.add(m.sender_id)
    
    conversations = []
    for partner_id in partners:
        partner = db.query(models.User).filter(models.User.id == partner_id).first()
        if not partner:
            continue
        
        # Last message
        last_msg = db.query(models.Message).filter(
            ((models.Message.sender_id == user.id) & (models.Message.receiver_id == partner_id)) |
            ((models.Message.sender_id == partner_id) & (models.Message.receiver_id == user.id))
        ).order_by(models.Message.created_at.desc()).first()
        
        unread = db.query(models.Message).filter(
            models.Message.sender_id   == partner_id,
            models.Message.receiver_id == user.id,
            models.Message.is_read     == False
        ).count()
        
        conversations.append({
            "partner_id":   partner_id,
            "partner_name": partner.name,
            "partner_avatar": partner.avatar,
            "partner_role": partner.role,
            "last_message": last_msg.content if last_msg else "",
            "last_time":    str(last_msg.created_at) if last_msg else "",
            "unread_count": unread,
        })
    
    return sorted(conversations, key=lambda x: x["last_time"], reverse=True)

@router.get("/dm/{partner_id}")
def get_dm_messages(
    partner_id: str,
    page: int = 1,
    limit: int = 50,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    messages = db.query(models.Message).filter(
        ((models.Message.sender_id == user.id) & (models.Message.receiver_id == partner_id)) |
        ((models.Message.sender_id == partner_id) & (models.Message.receiver_id == user.id))
    ).order_by(models.Message.created_at.asc()).offset((page-1)*limit).limit(limit).all()
    
    # Mark as read
    for m in messages:
        if m.receiver_id == user.id and not m.is_read:
            m.is_read = True
    db.commit()
    
    return [
        {
            "id":         m.id,
            "sender_id":  m.sender_id,
            "content":    m.content,
            "type":       m.type,
            "file_url":   m.file_url,
            "is_read":    m.is_read,
            "created_at": str(m.created_at),
        }
        for m in messages
    ]

@router.post("/send")
def send_message(
    data: SendMessage,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = models.Message(
        sender_id   = user.id,
        receiver_id = data.receiver_id,
        course_id   = data.course_id,
        content     = data.content,
        type        = data.type
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {
        "id":         msg.id,
        "sender_id":  msg.sender_id,
        "content":    msg.content,
        "created_at": str(msg.created_at)
    }

@router.get("/course/{course_id}")
def get_course_chat(
    course_id: str,
    page: int = 1,
    limit: int = 50,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    messages = db.query(models.Message).filter(
        models.Message.course_id == course_id
    ).order_by(models.Message.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    
    result = []
    for m in reversed(messages):
        sender = db.query(models.User).filter(models.User.id == m.sender_id).first()
        result.append({
            "id":           m.id,
            "sender_id":    m.sender_id,
            "sender_name":  sender.name if sender else "Unknown",
            "sender_avatar": sender.avatar if sender else None,
            "sender_role":  sender.role if sender else "student",
            "content":      m.content,
            "type":         m.type,
            "created_at":   str(m.created_at),
        })
    return result

@router.get("/unread-count")
def get_unread_count(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = db.query(models.Message).filter(
        models.Message.receiver_id == user.id,
        models.Message.is_read     == False
    ).count()
    return {"unread_count": count}
