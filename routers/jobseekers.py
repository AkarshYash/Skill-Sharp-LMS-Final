from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import re

from auth_utils import get_current_user
from database import get_db
import models
from services.ai_service import generate_quiz_questions, get_llm

router = APIRouter()


class ResumeBuilderRequest(BaseModel):
    target_role: Optional[str] = "Software Developer"
    summary: Optional[str] = ""
    skills: Optional[List[str]] = []
    projects: Optional[str] = ""
    experience: Optional[str] = ""
    education: Optional[str] = ""


class ResumeAnalyzeRequest(BaseModel):
    resume_text: str
    target_role: Optional[str] = "Target Role"


class AtsScoreRequest(BaseModel):
    resume_text: str
    job_description: str


class JobQuizRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
    num_questions: int = 5


class CodingAssessmentRequest(BaseModel):
    role: str = "Software Developer"
    language: str = "python"
    difficulty: str = "medium"


class TelephonicInterviewRequest(BaseModel):
    role: str = "Software Developer"
    company: Optional[str] = "the company"
    experience_level: Optional[str] = "fresher"


def _extract_json(content: str):
    content = content.strip()
    if "```json" in content:
        content = content.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in content:
        content = content.split("```", 1)[1].split("```", 1)[0].strip()
    return json.loads(content)


def _keywords(text: str) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z+#.\-]{2,}", text.lower())
    ignored = {
        "and", "the", "for", "with", "from", "that", "this", "will", "you",
        "are", "our", "your", "have", "has", "job", "role", "work", "team",
        "experience", "candidate", "skills", "using", "based", "ability",
    }
    counts = {}
    for word in words:
        if word not in ignored:
            counts[word] = counts.get(word, 0) + 1
    return [word for word, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:18]]


def _score_resume_against_jd(resume_text: str, job_description: str):
    resume_terms = set(_keywords(resume_text))
    jd_terms = _keywords(job_description)
    if not jd_terms:
        return 60, [], ["Paste a detailed job description for a stronger ATS score."]

    matched = [term for term in jd_terms if term in resume_terms]
    missing = [term for term in jd_terms if term not in resume_terms][:8]
    score = int(min(95, max(35, (len(matched) / max(len(jd_terms), 1)) * 100)))
    improvements = [
        "Add role-specific keywords naturally in your summary and project bullets.",
        "Use measurable achievements such as percentages, user counts, revenue, time saved, or performance gains.",
        "Group technical skills by category so ATS scanners can parse them cleanly.",
    ]
    if missing:
        improvements.insert(0, f"Add evidence for missing keywords: {', '.join(missing[:5])}.")
    return score, missing, improvements


@router.get("/dashboard")
def jobseeker_dashboard(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    latest_resume = db.query(models.Resume).filter(
        models.Resume.student_id == user.id
    ).order_by(models.Resume.created_at.desc()).first()
    sessions = db.query(models.InterviewSession).filter(
        models.InterviewSession.user_id == user.id
    ).order_by(models.InterviewSession.created_at.desc()).limit(5).all()

    return {
        "profile": {
            "name": user.name,
            "email": user.email,
            "student_type": user.student_type,
            "expertise": user.expertise,
        },
        "latest_resume": {
            "id": latest_resume.id,
            "title": latest_resume.title,
            "ats_score": latest_resume.ats_score,
            "created_at": str(latest_resume.created_at),
        } if latest_resume else None,
        "interview_sessions": [
            {
                "id": s.id,
                "ats_score": s.ats_score,
                "readiness_score": s.readiness_score,
                "created_at": str(s.created_at),
            } for s in sessions
        ],
        "tools": [
            "resume_builder",
            "resume_analysis",
            "ats_score",
            "ai_quiz_generator",
            "coding_assessment",
            "mock_video_interview",
            "telephonic_interview",
        ],
    }


@router.post("/resume-builder")
async def build_resume(
    data: ResumeBuilderRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skills = data.skills or []
    if user.expertise:
        skills.extend([s.strip() for s in user.expertise.split(",") if s.strip()])
    skills = list(dict.fromkeys(skills))

    fallback_resume = f"""# {user.name}
Email: {user.email}
Target Role: {data.target_role}

## Professional Summary
{data.summary or f"Motivated candidate preparing for {data.target_role} roles with a strong learning record, project mindset, and practical technical foundation."}

## Skills
{", ".join(skills) if skills else "Add your technical, communication, and role-specific skills here."}

## Projects
{data.projects or "- Add 2-3 projects with problem, technology, your contribution, and measurable result."}

## Experience
{data.experience or "- Add internship, freelance, academic, volunteer, or self-built experience here."}

## Education
{data.education or "- Add degree, institute, year, and relevant coursework."}
"""

    llm = get_llm(temperature=0.5)
    resume_text = fallback_resume
    if llm:
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content="You are an expert resume writer. Return a polished ATS-friendly resume in Markdown only."),
            HumanMessage(content=f"""Create a resume for:
Name: {user.name}
Email: {user.email}
Target role: {data.target_role}
Summary: {data.summary}
Skills: {', '.join(skills)}
Projects: {data.projects}
Experience: {data.experience}
Education: {data.education}
Keep it concise, professional, ATS-friendly, and ready to copy.""")
        ]
        try:
            result = await llm.ainvoke(messages)
            resume_text = result.content
        except Exception:
            resume_text = fallback_resume

    resume = models.Resume(
        student_id=user.id,
        title=f"{data.target_role} Resume",
        file_url="",
        parsed_data={
            "target_role": data.target_role,
            "skills": skills,
            "projects": data.projects,
            "experience": data.experience,
            "education": data.education,
        },
        ats_score=None,
        gap_analysis=None,
        ai_feedback="Generated from Jobseekers Resume Builder",
        is_current=True,
    )
    for old in db.query(models.Resume).filter(models.Resume.student_id == user.id, models.Resume.is_current == True).all():
        old.is_current = False
    db.add(resume)
    db.commit()
    db.refresh(resume)

    return {"resume_id": resume.id, "resume": resume_text, "format": "markdown"}


@router.post("/resume-analysis")
async def analyze_resume(data: ResumeAnalyzeRequest, user: models.User = Depends(get_current_user)):
    llm = get_llm(temperature=0.4)
    if llm:
        from langchain_core.messages import HumanMessage, SystemMessage
        try:
            result = await llm.ainvoke([
                SystemMessage(content="""You are a resume reviewer. Return ONLY JSON:
{"score": 82, "strengths": ["..."], "improvements": ["..."], "rewritten_summary": "..."}"""),
                HumanMessage(content=f"Target role: {data.target_role}\nResume:\n{data.resume_text}")
            ])
            return _extract_json(result.content)
        except Exception:
            pass

    keywords = _keywords(data.resume_text)
    return {
        "score": 72,
        "strengths": [
            "Resume has enough content to begin tailoring.",
            f"Detected relevant terms: {', '.join(keywords[:6]) or 'add more role-specific keywords'}."
        ],
        "improvements": [
            "Add a sharper professional summary aligned to the target role.",
            "Convert responsibilities into measurable achievement bullets.",
            "Add project links, portfolio links, GitHub, LinkedIn, or certifications where relevant.",
        ],
        "rewritten_summary": f"Motivated {data.target_role} candidate with practical skills, project experience, and a commitment to delivering measurable results.",
    }


@router.post("/ats-score")
async def ats_score(
    data: AtsScoreRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    score, missing, improvements = _score_resume_against_jd(data.resume_text, data.job_description)

    llm = get_llm(temperature=0.3)
    if llm:
        from langchain_core.messages import HumanMessage, SystemMessage
        try:
            result = await llm.ainvoke([
                SystemMessage(content="""You are an ATS resume scanner. Return ONLY JSON:
{"ats_score": 80, "readiness_score": 76, "missing_keywords": ["..."], "improvements": ["..."], "recommended_courses": ["..."]}"""),
                HumanMessage(content=f"RESUME:\n{data.resume_text}\n\nJOB DESCRIPTION:\n{data.job_description}")
            ])
            parsed = _extract_json(result.content)
            score = int(parsed.get("ats_score", score))
            missing = parsed.get("missing_keywords", missing)
            improvements = parsed.get("improvements", improvements)
            recommended_courses = parsed.get("recommended_courses", [])
        except Exception:
            recommended_courses = []
    else:
        recommended_courses = []

    resume = models.Resume(
        student_id=user.id,
        title="ATS Scanned Resume",
        file_url="",
        parsed_data={"keywords": _keywords(data.resume_text)},
        ats_score=score,
        gap_analysis="\n".join(improvements),
        ai_feedback=f"Missing keywords: {', '.join(missing) if missing else 'None'}",
        is_current=True,
    )
    for old in db.query(models.Resume).filter(models.Resume.student_id == user.id, models.Resume.is_current == True).all():
        old.is_current = False
    db.add(resume)
    db.commit()

    return {
        "ats_score": score,
        "readiness_score": min(100, score + 5),
        "missing_keywords": missing,
        "improvements": improvements,
        "recommended_courses": recommended_courses or ["System Design", "Data Structures", "Interview Communication"],
    }


@router.post("/quiz-generator")
async def job_quiz(data: JobQuizRequest, user: models.User = Depends(get_current_user)):
    count = max(1, min(data.num_questions, 15))
    questions = await generate_quiz_questions(data.topic, count, data.difficulty)
    return {
        "title": f"Job Prep Quiz: {data.topic}",
        "topic": data.topic,
        "difficulty": data.difficulty,
        "questions": questions,
    }


@router.post("/coding-assessment")
async def coding_assessment(data: CodingAssessmentRequest, user: models.User = Depends(get_current_user)):
    llm = get_llm(temperature=0.5)
    if llm:
        from langchain_core.messages import HumanMessage, SystemMessage
        try:
            result = await llm.ainvoke([
                SystemMessage(content="""Create a coding assessment. Return ONLY JSON:
{"title": "...", "duration_minutes": 45, "problem": "...", "input_format": "...", "output_format": "...", "constraints": ["..."], "sample_tests": [{"input": "...", "output": "..."}], "rubric": ["..."]}"""),
                HumanMessage(content=f"Role: {data.role}\nLanguage: {data.language}\nDifficulty: {data.difficulty}")
            ])
            return _extract_json(result.content)
        except Exception:
            pass

    return {
        "title": f"{data.role} Coding Assessment",
        "duration_minutes": 45,
        "language": data.language,
        "problem": "Given a list of integers, return the length of the longest consecutive sequence in O(n) time.",
        "input_format": "An array of integers.",
        "output_format": "A single integer representing the longest consecutive sequence length.",
        "constraints": ["Use O(n) time complexity.", "Avoid sorting for the optimal solution.", "Explain edge cases."],
        "sample_tests": [{"input": "[100,4,200,1,3,2]", "output": "4"}],
        "rubric": ["Correctness", "Complexity", "Edge cases", "Code readability", "Explanation quality"],
    }


@router.post("/telephonic-interview")
async def telephonic_interview(data: TelephonicInterviewRequest, user: models.User = Depends(get_current_user)):
    llm = get_llm(temperature=0.5)
    if llm:
        from langchain_core.messages import HumanMessage, SystemMessage
        try:
            result = await llm.ainvoke([
                SystemMessage(content="""Create telephonic interview preparation. Return ONLY JSON:
{"opening_pitch": "...", "questions": [{"question": "...", "answer_tip": "..."}], "salary_answer": "...", "closing_script": "..."}"""),
                HumanMessage(content=f"Candidate: {user.name}\nRole: {data.role}\nCompany: {data.company}\nExperience: {data.experience_level}")
            ])
            return _extract_json(result.content)
        except Exception:
            pass

    return {
        "opening_pitch": f"Hello, my name is {user.name}. I am interested in the {data.role} role at {data.company}. I have been preparing with relevant skills and projects, and I would be happy to discuss how I can contribute.",
        "questions": [
            {"question": "Tell me about yourself.", "answer_tip": "Keep it under 60 seconds: background, skills, one project, target role."},
            {"question": "Why are you looking for this role?", "answer_tip": "Connect your skills and career direction to the company and role."},
            {"question": "What is your notice period or availability?", "answer_tip": "Answer directly and professionally with exact availability."},
        ],
        "salary_answer": "I am open to a fair offer based on the role, responsibilities, and market standards. I would like to understand the complete compensation range for this position.",
        "closing_script": "Thank you for the call. I appreciate your time and I am interested in the next steps. Please let me know if you need any more details from my side.",
    }
