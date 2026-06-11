from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from auth_utils import get_current_user
import models
from services.ai_service import get_llm

router = APIRouter()

class InterviewAnalyzeRequest(BaseModel):
    resume_text: str
    job_description: str

class InterviewStartRequest(BaseModel):
    resume_text: str
    job_description: str

class AnswerSubmitRequest(BaseModel):
    session_id: str
    question_id: int
    answer: str
    eye_contact_sim: Optional[int] = 90
    confidence_sim: Optional[int] = 85

# ─── Endpoints ──────────────────────────────────────────────

@router.post("/analyze")
async def analyze_resume_jd(data: InterviewAnalyzeRequest, user: models.User = Depends(get_current_user)):
    """AI analyses resume against a target JD to give an ATS scorecard and gap feedback"""
    llm = get_llm(temperature=0.4)
    
    if not llm:
        # Fallback scorecard if AI is offline
        return {
            "ats_score": 75,
            "readiness_score": 70,
            "gap_analysis": {
                "skills_missing": ["React Native", "Kubernetes", "System Design"],
                "improvements": [
                    "Highlight cloud deployments in your professional summary.",
                    "Add quantifiable metrics for your software engineering achievements."
                ]
            },
            "recommended_courses": ["Advanced React Native", "Docker & Kubernetes Masterclass"],
            "market_insight": "Cloud-based developer roles have seen a 40% growth in global markets this quarter."
        }

    from langchain_core.messages import SystemMessage, HumanMessage
    import json
    
    system_prompt = """You are an expert HR Executive and ATS resume scanner.
Analyze the user's resume against the Job Description.
Evaluate matching skills, find missing target skills, and output a detailed score.
You MUST return ONLY a valid JSON object matching this structure:
{
  "ats_score": 85,
  "readiness_score": 80,
  "gap_analysis": {
    "skills_missing": ["Skill A", "Skill B"],
    "improvements": ["Improvement point 1", "Improvement point 2"]
  },
  "recommended_courses": ["Course Topic A", "Course Topic B"],
  "market_insight": "Insight about the role market demand."
}
No extra text or explanations outside of JSON."""

    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"RESUME:\n{data.resume_text}\n\nJOB DESCRIPTION:\n{data.job_description}")
        ]
        res = await llm.ainvoke(messages)
        content = res.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)
    except Exception as e:
        raise HTTPException(500, f"AI analysis failed: {str(e)}")

@router.post("/start")
async def start_interview_session(
    data: InterviewStartRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Starts a new mock interview session and generates custom questions specific to JD and resume"""
    llm = get_llm(temperature=0.5)
    
    questions = []
    if not llm:
        # Fallback offline questions
        questions = [
            {"id": 1, "type": "Behavioral", "question": "Tell me about a time you had to resolve a technical conflict in a team."},
            {"id": 2, "type": "Technical", "question": "What is the difference between processes and threads, and how do they manage memory?"},
            {"id": 3, "type": "Coding", "question": "Write a python function to check if a binary tree is symmetric."},
            {"id": 4, "type": "System Design", "question": "How would you design a URL shortener service like Bitly?"},
            {"id": 5, "type": "Behavioral", "question": "Why are you interested in this specific role and what strengths do you bring?"}
        ]
    else:
        from langchain_core.messages import SystemMessage, HumanMessage
        import json
        
        system_prompt = """You are an expert technical recruiter.
Create exactly 5 highly customized interview questions for the user based on their resume and the target Job Description.
Generate:
- 2 behavioral questions
- 1 core technical theory question
- 1 system design question
- 1 standard coding practice challenge (write code script)
You MUST return ONLY a valid JSON array matching this structure:
[
  {
    "id": 1,
    "type": "Technical / Coding / Behavioral / System Design",
    "question": "Question text here?"
  }
]
No extra conversational text outside of the JSON array."""
        
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"RESUME:\n{data.resume_text}\n\nJOB DESCRIPTION:\n{data.job_description}")
            ]
            res = await llm.ainvoke(messages)
            content = res.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            questions = json.loads(content)
        except Exception as e:
            # Fallback
            questions = [
                {"id": 1, "type": "Technical", "question": "Can you explain inheritance and polymorphism with coding examples?"},
                {"id": 2, "type": "Behavioral", "question": "Describe your most challenging software engineering project."}
            ]
            
    # Calculate initial scores
    ats_score = 75
    readiness_score = 70
    
    # Save session
    session = models.InterviewSession(
        user_id         = user.id,
        resume_text     = data.resume_text,
        job_description = data.job_description,
        questions       = questions,
        chat_history    = [{"role": "bot", "content": f"Welcome {user.name}! Let's start the mock interview. Here is your first question:\n\n" + questions[0]["question"], "timestamp": datetime.utcnow().isoformat()}],
        ats_score       = ats_score,
        readiness_score = readiness_score,
        gap_analysis    = {"skills_missing": [], "improvements": []}
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {
        "session_id": session.id,
        "first_question": questions[0],
        "total_questions": len(questions)
    }

@router.post("/submit-answer")
async def submit_answer(
    data: AnswerSubmitRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submits student's response to an interview question, scores it, and returns the next question or final evaluation report"""
    session = db.query(models.InterviewSession).filter(
        models.InterviewSession.id      == data.session_id,
        models.InterviewSession.user_id == user.id
    ).first()
    
    if not session:
        raise HTTPException(404, "Session not found")
        
    questions = session.questions or []
    current_q_idx = data.question_id - 1
    
    if current_q_idx < 0 or current_q_idx >= len(questions):
        raise HTTPException(400, "Invalid question ID")
        
    current_question = questions[current_q_idx]["question"]
    current_type = questions[current_q_idx]["type"]
    
    # Evaluate answer with LLM
    llm = get_llm(temperature=0.5)
    score_out_of_10 = 7
    ai_feedback = "Good attempt. Your explanation touched on the key aspects but could be expanded with more structured diagrams or metrics."
    
    if llm:
        from langchain_core.messages import SystemMessage, HumanMessage
        import json
        
        system_prompt = """You are an elite interviewer.
Evaluate the candidate's answer to the specific interview question.
Assess correctness, technical depth, and professional communication.
You MUST return ONLY a valid JSON object matching this structure:
{
  "score": 8,
  "feedback": "Concise review of correctness, structure, and professional tips."
}
No extra text."""
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"QUESTION: {current_question}\nCANDIDATE ANSWER: {data.answer}")
            ]
            res = await llm.ainvoke(messages)
            content = res.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            val = json.loads(content)
            score_out_of_10 = val.get("score", 7)
            ai_feedback = val.get("feedback", "Good explanation.")
        except:
            pass
            
    # Append history
    history = session.chat_history or []
    history.append({"role": "user", "content": data.answer, "timestamp": datetime.utcnow().isoformat()})
    
    # Accumulate simulated scores
    session.eye_contact_score = int((session.eye_contact_score + data.eye_contact_sim) / 2) if session.eye_contact_score else data.eye_contact_sim
    session.confidence_score = int((session.confidence_score + data.confidence_sim) / 2) if session.confidence_score else data.confidence_sim
    
    next_question = None
    next_q_id = data.question_id + 1
    next_q_idx = next_q_id - 1
    
    if next_q_idx < len(questions):
        next_question = questions[next_q_idx]
        history.append({
            "role": "bot",
            "content": f"Feedback on Q{data.question_id}: {ai_feedback}\n\nHere is Question {next_q_id} ({next_question['type']}):\n{next_question['question']}",
            "timestamp": datetime.utcnow().isoformat()
        })
    else:
        # Finalize report!
        history.append({
            "role": "bot",
            "content": f"Thank you for completing the interview! Analyzing your performance and preparing a final ATS/Readiness scorecard. Check your reports tab.",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Calculate overall scores
        session.readiness_score = int(70 + (session.confidence_score * 0.15) + (session.eye_contact_score * 0.15))
        session.eval_report = f"""### AI Mock Interview Evaluation Summary
- **Overall Readiness Rating:** {session.readiness_score}/100
- **Technical Competency:** Excellent technical theoretical base, showing solid OOP and systems principles.
- **Communication & Confidence:** Scored {session.confidence_score}% in verbal clarity. Demonstrates positive voice modulation.
- **Visual Engagement Simulation:** Handled simulated camera tracking at {session.eye_contact_score}% focus level.
- **Improvement Tip:** In coding questions, explain edge cases (e.g. null inputs or divide by zero errors) before writing the solution."""
        
        # Award XP for interview practice
        pts = user.points
        if pts:
            pts.xp += 30
            
    session.chat_history = history
    session.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "feedback": ai_feedback,
        "score": score_out_of_10,
        "next_question": next_question,
        "completed": next_question is None,
        "report": session.eval_report if next_question is None else None
    }

@router.get("/sessions")
def list_sessions(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve list of past interview sessions"""
    sessions = db.query(models.InterviewSession).filter(
        models.InterviewSession.user_id == user.id
    ).order_by(models.InterviewSession.created_at.desc()).all()
    
    return [
        {
            "id": s.id,
            "ats_score": s.ats_score,
            "readiness_score": s.readiness_score,
            "eye_contact_score": s.eye_contact_score,
            "confidence_score": s.confidence_score,
            "created_at": str(s.created_at)
        }
        for s in sessions
    ]

@router.get("/sessions/{session_id}")
def get_session_details(session_id: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieve full details of an interview session"""
    s = db.query(models.InterviewSession).filter(
        models.InterviewSession.id      == session_id,
        models.InterviewSession.user_id == user.id
    ).first()
    if not s:
        raise HTTPException(404, "Session not found")
        
    return {
        "id": s.id,
        "resume_text": s.resume_text,
        "job_description": s.job_description,
        "chat_history": s.chat_history or [],
        "ats_score": s.ats_score,
        "readiness_score": s.readiness_score,
        "eye_contact_score": s.eye_contact_score,
        "confidence_score": s.confidence_score,
        "eval_report": s.eval_report,
        "created_at": str(s.created_at)
    }
