from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth_utils import get_current_user
import models

router = APIRouter()

@router.post("/generate")
async def generate_resume(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI-powered resume generation"""
    completed = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == user.id,
        models.Enrollment.completed  == True
    ).all()
    
    courses = []
    for e in completed:
        if e.course:
            courses.append({
                "title":     e.course.title,
                "level":     e.course.level,
                "completed": True,
            })
    
    user_data = {
        "name":        user.name,
        "email":       user.email,
        "bio":         user.bio or "",
        "expertise":   user.expertise or "",
        "linkedin_url": user.linkedin_url or "",
        "github_url":  user.github_url or "",
    }
    
    try:
        from services.ai_service import generate_resume as gen_resume
        resume_content = await gen_resume(user_data, courses)
        return {"resume": resume_content, "format": "markdown"}
    except Exception as e:
        raise HTTPException(500, f"Resume generation failed: {str(e)}")

@router.post("/generate-cover-letter")
async def generate_cover_letter(
    job_title: str,
    company:   str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI cover letter generation"""
    from services.ai_service import get_llm
    llm = get_llm(temperature=0.7)
    
    if not llm:
        raise HTTPException(503, "AI service unavailable")
    
    from langchain_core.messages import HumanMessage, SystemMessage
    messages = [
        SystemMessage(content="You are a professional career coach writing compelling cover letters."),
        HumanMessage(content=f"""Write a professional cover letter for:
Name: {user.name}
Applying for: {job_title} at {company}
Bio: {user.bio or 'Passionate learner and developer'}
Skills: {user.expertise or 'Technology and innovation'}

Write a compelling, personalized cover letter in a professional tone.""")
    ]
    
    try:
        result = await llm.ainvoke(messages)
        return {"cover_letter": result.content}
    except Exception as e:
        raise HTTPException(500, str(e))
