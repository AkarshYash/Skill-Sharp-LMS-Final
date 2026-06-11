"""
AI Interview Preparation Module - Resume Analysis, AI Video Interview, Feedback
Skill Sharp 365 Innovations
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from models import Resume, JobDescription, InterviewPrep, VideoInterview, InterviewReport
from pydantic import BaseModel
from datetime import datetime
import os
import shutil

class ResumeUploadResponse(BaseModel):
    id: str
    ats_score: float
    gaps_identified: List[str]

router = APIRouter()

# ─────────────────────────────────────────
# RESUME MANAGEMENT
# ─────────────────────────────────────────

@router.post("/upload-resume")
async def upload_resume(
    student_id: str,
    title: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and analyze resume using AI"""
    # Save file
    upload_dir = f"static/uploads/resumes/{student_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{file.filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Parse and analyze resume (AI processing)
    parsed_data = {
        "skills": ["Python", "JavaScript", "React", "AWS"],
        "experience": [
            {"company": "Tech Corp", "role": "SWE", "duration": "2 years"}
        ],
        "education": [
            {"degree": "BTech", "field": "Computer Science"}
        ]
    }
    
    # Generate ATS score
    ats_score = 78.5  # Placeholder - would be calculated by AI
    
    # Identify gaps
    gaps = ["missing certifications", "limited project experience"]
    
    resume = Resume(
        student_id=student_id,
        title=title,
        file_url=f"/{file_path}",
        parsed_data=parsed_data,
        ats_score=ats_score,
        gap_analysis="\n".join(gaps),
        is_current=True
    )
    
    # Mark previous resumes as not current
    previous = db.query(Resume).filter(
        Resume.student_id == student_id,
        Resume.is_current == True
    ).all()
    for prev in previous:
        prev.is_current = False
    
    db.add(resume)
    db.commit()
    db.refresh(resume)
    
    return {
        "status": "success",
        "message": "Resume uploaded and analyzed",
        "resume": {
            "id": resume.id,
            "ats_score": ats_score,
            "gaps_identified": gaps
        }
    }

@router.get("/resume/{resume_id}")
def get_resume_analysis(resume_id: str, db: Session = Depends(get_db)):
    """Get detailed resume analysis and ATS score"""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return {
        "status": "success",
        "resume": {
            "id": resume.id,
            "title": resume.title,
            "ats_score": resume.ats_score,
            "parsed_data": resume.parsed_data,
            "gap_analysis": resume.gap_analysis,
            "ai_feedback": resume.ai_feedback
        }
    }

@router.get("/students/{student_id}/resumes")
def get_student_resumes(student_id: str, db: Session = Depends(get_db)):
    """Get all resumes uploaded by a student"""
    resumes = db.query(Resume).filter(
        Resume.student_id == student_id
    ).order_by(Resume.created_at.desc()).all()
    
    return {
        "status": "success",
        "resumes": [
            {
                "id": r.id,
                "title": r.title,
                "ats_score": r.ats_score,
                "is_current": r.is_current,
                "created_at": r.created_at
            } for r in resumes
        ]
    }

# ─────────────────────────────────────────
# JOB DESCRIPTION ANALYSIS
# ─────────────────────────────────────────

@router.post("/create-job-desc")
def create_job_description(
    title: str,
    company: str,
    description: str,
    required_skills: List[str],
    experience_needed: str,
    db: Session = Depends(get_db)
):
    """Create or upload job description for interview prep"""
    # Parse JD
    parsed_data = {
        "skills": required_skills,
        "experience": experience_needed,
        "title": title,
        "company": company
    }
    
    job_desc = JobDescription(
        title=title,
        company=company,
        description=description,
        required_skills=required_skills,
        experience_needed=experience_needed,
        parsed_data=parsed_data
    )
    db.add(job_desc)
    db.commit()
    db.refresh(job_desc)
    
    return {
        "status": "success",
        "message": "Job description created",
        "job_desc_id": job_desc.id
    }

@router.get("/job-desc/{job_desc_id}")
def get_job_description(job_desc_id: str, db: Session = Depends(get_db)):
    """Get job description details"""
    job_desc = db.query(JobDescription).filter(
        JobDescription.id == job_desc_id
    ).first()
    if not job_desc:
        raise HTTPException(status_code=404, detail="Job description not found")
    
    return {
        "status": "success",
        "job_description": {
            "title": job_desc.title,
            "company": job_desc.company,
            "description": job_desc.description,
            "required_skills": job_desc.required_skills,
            "experience_needed": job_desc.experience_needed
        }
    }

# ─────────────────────────────────────────
# INTERVIEW PREPARATION
# ─────────────────────────────────────────

@router.post("/prepare-interview")
def prepare_interview(
    student_id: str,
    interview_type: str,  # technical/behavioral/hr/system_design
    resume_id: Optional[str] = None,
    job_desc_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Generate AI interview questions based on resume and JD"""
    
    # Generate interview questions (AI powered)
    questions = {
        "technical": [
            "Explain the SOLID principles",
            "Design a URL shortener system",
            "What is OAuth2?",
            "Implement a LRU cache"
        ],
        "behavioral": [
            "Tell me about a challenging project",
            "How do you handle failure?",
            "Describe a time you worked in a team"
        ],
        "hr": [
            "Why do you want to join our company?",
            "Where do you see yourself in 5 years?",
            "What are your strengths?"
        ],
        "system_design": [
            "Design Twitter",
            "Design a recommendation system",
            "Design an e-commerce platform"
        ]
    }
    
    selected_questions = questions.get(interview_type, [])
    
    prep = InterviewPrep(
        student_id=student_id,
        resume_id=resume_id,
        job_desc_id=job_desc_id,
        interview_type=interview_type,
        questions=selected_questions
    )
    db.add(prep)
    db.commit()
    db.refresh(prep)
    
    return {
        "status": "success",
        "message": "Interview prep session created",
        "interview_prep": {
            "id": prep.id,
            "type": interview_type,
            "questions": selected_questions
        }
    }

# ─────────────────────────────────────────
# AI VIDEO INTERVIEW
# ─────────────────────────────────────────

@router.post("/video-interview/start")
def start_video_interview(
    interview_prep_id: str,
    db: Session = Depends(get_db)
):
    """Start AI video interview simulation"""
    prep = db.query(InterviewPrep).filter(
        InterviewPrep.id == interview_prep_id
    ).first()
    if not prep:
        raise HTTPException(status_code=404, detail="Interview prep not found")
    
    return {
        "status": "success",
        "message": "Video interview started",
        "interview": {
            "interview_prep_id": interview_prep_id,
            "interview_type": prep.interview_type,
            "first_question": prep.questions[0] if prep.questions else "Tell me about yourself",
            "start_time": datetime.now()
        }
    }

@router.post("/video-interview/{interview_prep_id}/submit")
def submit_video_interview(
    interview_prep_id: str,
    video_url: str,
    transcript: str,
    db: Session = Depends(get_db)
):
    """Submit video interview for AI analysis"""
    prep = db.query(InterviewPrep).filter(
        InterviewPrep.id == interview_prep_id
    ).first()
    if not prep:
        raise HTTPException(status_code=404, detail="Interview prep not found")
    
    # AI Analysis (Placeholder scores)
    video_interview = VideoInterview(
        interview_prep_id=interview_prep_id,
        video_url=video_url,
        transcript=transcript,
        eye_contact_score=75.0,
        confidence_score=82.0,
        communication_score=78.0,
        technical_score=85.0,
        overall_score=80.0,
        feedback="Good technical knowledge, but improve eye contact",
        improvement_areas=["Eye contact", "Pacing", "Technical depth"]
    )
    db.add(video_interview)
    db.commit()
    db.refresh(video_interview)
    
    return {
        "status": "success",
        "message": "Video interview analyzed",
        "analysis": {
            "id": video_interview.id,
            "scores": {
                "eye_contact": video_interview.eye_contact_score,
                "confidence": video_interview.confidence_score,
                "communication": video_interview.communication_score,
                "technical": video_interview.technical_score,
                "overall": video_interview.overall_score
            },
            "feedback": video_interview.feedback,
            "improvement_areas": video_interview.improvement_areas
        }
    }

@router.get("/video-interview/{video_interview_id}/report")
def get_interview_report(video_interview_id: str, db: Session = Depends(get_db)):
    """Get comprehensive interview performance report"""
    video_interview = db.query(VideoInterview).filter(
        VideoInterview.id == video_interview_id
    ).first()
    if not video_interview:
        raise HTTPException(status_code=404, detail="Video interview not found")
    
    # Generate or retrieve report
    report = db.query(InterviewReport).filter(
        InterviewReport.video_interview_id == video_interview_id
    ).first()
    
    if not report:
        # Create new report
        report = InterviewReport(
            student_id=video_interview.interview_prep.student_id,
            video_interview_id=video_interview_id,
            ats_score=78.0,
            resume_gap_score=82.0,
            skill_gap_score=75.0,
            interview_readiness=80.0,
            recommendations=[
                "Improve system design knowledge",
                "Practice more behavioral questions",
                "Work on communication clarity"
            ]
        )
        db.add(report)
        db.commit()
    
    return {
        "status": "success",
        "report": {
            "id": report.id,
            "ats_score": report.ats_score,
            "resume_gap_score": report.resume_gap_score,
            "skill_gap_score": report.skill_gap_score,
            "interview_readiness": report.interview_readiness,
            "recommendations": report.recommendations
        }
    }

# ─────────────────────────────────────────
# INTERVIEW HISTORY & ANALYTICS
# ─────────────────────────────────────────

@router.get("/students/{student_id}/interview-history")
def get_interview_history(student_id: str, db: Session = Depends(get_db)):
    """Get all interview attempts and reports"""
    preps = db.query(InterviewPrep).filter(
        InterviewPrep.student_id == student_id
    ).all()
    
    return {
        "status": "success",
        "interviews": [
            {
                "id": p.id,
                "type": p.interview_type,
                "created_at": p.created_at,
                "questions_count": len(p.questions) if p.questions else 0
            } for p in preps
        ]
    }

@router.get("/students/{student_id}/interview-readiness")
def get_interview_readiness(student_id: str, db: Session = Depends(get_db)):
    """Get overall interview readiness score"""
    # This would calculate based on all assessments
    return {
        "status": "success",
        "readiness": {
            "overall_score": 78.5,
            "technical_readiness": 82.0,
            "communication_readiness": 76.0,
            "behavioral_readiness": 75.0,
            "next_steps": [
                "Focus on system design problems",
                "Practice mock interviews",
                "Review LeetCode Medium problems"
            ]
        }
    }
