from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict
from pydantic import BaseModel
import models
from database import get_db
from auth_utils import get_current_user

router = APIRouter()

# Schema
class GroupCreate(BaseModel):
    name: str
    batch_id: str = None
    course_id: str = None

class MessageCreate(BaseModel):
    content: str
    attachment: str = None

# Active websocket connections per group
active_connections: Dict[str, List[WebSocket]] = {}

@router.post("/")
def create_group(group: GroupCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role not in ["faculty", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to create groups")
        
    db_group = models.GroupChat(
        name=group.name,
        batch_id=group.batch_id,
        course_id=group.course_id,
        created_by=current_user.id
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@router.get("/")
def list_groups(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Very basic listing for now, normally filtered by enrollment
    groups = db.query(models.GroupChat).all()
    return groups

@router.get("/{group_id}/messages")
def get_messages(group_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    messages = db.query(models.GroupMessage).filter(models.GroupMessage.group_id == group_id).order_by(models.GroupMessage.created_at).all()
    result = []
    for m in messages:
        sender = db.query(models.User).filter(models.User.id == m.sender_id).first()
        result.append({
            "id": m.id,
            "content": m.content,
            "attachment": m.attachment,
            "created_at": str(m.created_at),
            "sender_name": sender.name if sender else "Unknown",
            "sender_id": m.sender_id
        })
    return result

@router.websocket("/ws/{group_id}")
async def websocket_endpoint(websocket: WebSocket, group_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    if group_id not in active_connections:
        active_connections[group_id] = []
    active_connections[group_id].append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Expecting: {"sender_id": "...", "content": "..."}
            
            # Save to DB
            new_msg = models.GroupMessage(
                group_id=group_id,
                sender_id=data.get("sender_id"),
                content=data.get("content")
            )
            db.add(new_msg)
            db.commit()
            db.refresh(new_msg)
            
            sender = db.query(models.User).filter(models.User.id == new_msg.sender_id).first()
            
            # Broadcast to everyone in group
            broadcast_data = {
                "id": new_msg.id,
                "content": new_msg.content,
                "sender_id": new_msg.sender_id,
                "sender_name": sender.name if sender else "Unknown",
                "created_at": str(new_msg.created_at)
            }
            
            for connection in active_connections[group_id]:
                await connection.send_json(broadcast_data)
                
    except WebSocketDisconnect:
        active_connections[group_id].remove(websocket)
