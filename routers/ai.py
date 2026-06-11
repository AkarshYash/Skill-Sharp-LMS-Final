from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from auth_utils import get_current_user
import models

router = APIRouter()

class ChatMessage(BaseModel):
    message: str
    course_id: Optional[str] = None
    session_id: Optional[str] = None

class NewSession(BaseModel):
    title: Optional[str] = "New Chat"
    course_id: Optional[str] = None
    topic: Optional[str] = None

# ─── AI Tutor Sessions ────────────────────────────

@router.get("/sessions")
def get_sessions(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(models.AITutorSession).filter(
        models.AITutorSession.user_id == user.id
    ).order_by(models.AITutorSession.updated_at.desc()).limit(20).all()
    
    return [
        {
            "id":         s.id,
            "title":      s.title,
            "topic":      s.topic,
            "course_id":  s.course_id,
            "message_count": len(s.messages) if s.messages else 0,
            "created_at": str(s.created_at),
            "updated_at": str(s.updated_at),
        }
        for s in sessions
    ]

@router.post("/sessions")
def create_session(
    data: NewSession,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = models.AITutorSession(
        user_id   = user.id,
        title     = data.title,
        course_id = data.course_id,
        topic     = data.topic,
        messages  = []
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"id": session.id, "title": session.title}

@router.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(models.AITutorSession).filter(
        models.AITutorSession.id      == session_id,
        models.AITutorSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(404, "Session not found")
    
    return {
        "id":        session.id,
        "title":     session.title,
        "topic":     session.topic,
        "course_id": session.course_id,
        "messages":  session.messages or [],
    }

@router.post("/chat")
async def ai_chat(
    data: ChatMessage,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Main AI tutor chat endpoint with LangChain + RAG"""
    
    # Get or create session
    if data.session_id:
        session = db.query(models.AITutorSession).filter(
            models.AITutorSession.id      == data.session_id,
            models.AITutorSession.user_id == user.id
        ).first()
    else:
        session = models.AITutorSession(
            user_id   = user.id,
            title     = data.message[:50],
            course_id = data.course_id,
            messages  = []
        )
        db.add(session)
        db.flush()
    
    if not session:
        raise HTTPException(404, "Session not found")
    
    # Get chat history
    history = session.messages or []
    
    try:
        from services.ai_service import ai_tutor_chat
        response = await ai_tutor_chat(
            user_message = data.message,
            chat_history = history,
            course_id    = data.course_id or session.course_id
        )
    except Exception as e:
        response = f"I'm having trouble connecting right now. Please try again. ({str(e)[:100]})"
    
    # Update session
    timestamp = datetime.utcnow().isoformat()
    new_history = history + [
        {"role": "user",      "content": data.message, "timestamp": timestamp},
        {"role": "assistant", "content": response,     "timestamp": timestamp},
    ]
    session.messages   = new_history
    session.updated_at = datetime.utcnow()
    
    # Award XP for using AI tutor
    pts = user.points
    if pts and len(new_history) % 10 == 0:  # every 5 messages
        pts.xp += 5
    
    db.commit()
    
    return {
        "response":   response,
        "session_id": session.id,
        "message_count": len(new_history)
    }

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(models.AITutorSession).filter(
        models.AITutorSession.id      == session_id,
        models.AITutorSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(404, "Session not found")
    db.delete(session)
    db.commit()
    return {"message": "Session deleted"}

@router.get("/rag/status/{course_id}")
def rag_status(
    course_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check RAG indexing status for a course"""
    try:
        from services.rag_service import get_index_stats
        stats = get_index_stats(course_id)
    except:
        stats = {"total_chunks": 0, "indexed": False}
    
    notes = db.query(models.LectureNote).filter(
        models.LectureNote.course_id == course_id
    ).all()
    
    return {
        "course_id":    course_id,
        "total_notes":  len(notes),
        "indexed_notes": sum(1 for n in notes if n.is_indexed),
        "vector_chunks": stats.get("total_chunks", 0),
        "rag_active":   stats.get("indexed", False)
    }

@router.post("/generate-summary")
async def generate_content_summary(
    content: str,
    title: str = "Content",
    user: models.User = Depends(get_current_user)
):
    """Generate AI summary for any content"""
    try:
        from services.ai_service import generate_lecture_summary
        summary = await generate_lecture_summary(title, content)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/study-tips")
async def get_study_tips(
    subject: str,
    level: str = "beginner",
    user: models.User = Depends(get_current_user)
):
    """Get personalized study tips"""
    from services.ai_service import get_llm
    llm = get_llm(temperature=0.8)
    
    if not llm:
        return {"tips": [
            "Review notes within 24 hours of learning",
            "Use the Pomodoro technique for focused study",
            "Practice active recall instead of passive reading",
            "Teach concepts to others to deepen understanding",
            "Take regular breaks to avoid burnout"
        ]}
    
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content="You are an expert study coach. Provide exactly 5 practical study tips as a JSON array of strings."),
            HumanMessage(content=f"Study tips for {subject} at {level} level. Return ONLY a JSON array: [\"tip1\", \"tip2\", ...]")
        ]
        result = await llm.ainvoke(messages)
        import json
        content = result.content.strip()
        if "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            if content.startswith("json"):
                content = content[4:].strip()
        tips = json.loads(content)
        return {"tips": tips}
    except Exception as e:
        return {"tips": ["Focus on fundamentals", "Practice regularly", "Seek help when stuck", "Review before tests", "Stay consistent"]}
