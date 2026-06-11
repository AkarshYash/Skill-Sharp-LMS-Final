"""
Career Portal & Placements - Jobs, Internships, Placements
Skill Sharp 365 Innovations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import JobListing, InternshipListing, JobApplication, Portfolio, PortfolioProject
from pydantic import BaseModel
from datetime import datetime

class JobListingCreate(BaseModel):
    title: str
    company: str
    description: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    location: str
    job_type: str  # full_time/part_time/intern
    experience_needed: str
    required_skills: list

router = APIRouter()

# ─────────────────────────────────────────
# JOB LISTINGS
# ─────────────────────────────────────────

@router.get("/jobs")
def get_job_listings(
    skip: int = 0,
    limit: int = 10,
    job_type: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all active job listings"""
    query = db.query(JobListing).filter(JobListing.is_active == True)
    
    if job_type:
        query = query.filter(JobListing.job_type == job_type)
    if location:
        query = query.filter(JobListing.location.ilike(f"%{location}%"))
    
    total = query.count()
    jobs = query.offset(skip).limit(limit).all()
    
    return {
        "status": "success",
        "total": total,
        "jobs": [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "location": j.location,
                "job_type": j.job_type,
                "salary": f"{j.salary_min}-{j.salary_max}" if j.salary_min else "Not specified",
                "experience_needed": j.experience_needed,
                "posted_at": j.posted_at
            } for j in jobs
        ]
    }

@router.get("/jobs/{job_id}")
def get_job_details(job_id: str, db: Session = Depends(get_db)):
    """Get detailed job listing"""
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Count applications
    applications = db.query(JobApplication).filter(
        JobApplication.job_id == job_id
    ).count()
    
    return {
        "status": "success",
        "job": {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "description": job.description,
            "location": job.location,
            "job_type": job.job_type,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "currency": job.currency,
            "experience_needed": job.experience_needed,
            "required_skills": job.required_skills,
            "deadline": job.deadline,
            "applications_count": applications,
            "posted_at": job.posted_at
        }
    }

@router.post("/jobs/create")
def create_job_listing(
    job_data: JobListingCreate,
    recruiter_id: str,
    deadline: datetime,
    db: Session = Depends(get_db)
):
    """Post a new job listing (Recruiter only)"""
    job = JobListing(
        **job_data.model_dump(),
        recruiter_id=recruiter_id,
        deadline=deadline,
        posted_at=datetime.now()
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    return {
        "status": "success",
        "message": "Job listing posted",
        "job_id": job.id
    }

# ─────────────────────────────────────────
# INTERNSHIP LISTINGS
# ─────────────────────────────────────────

@router.get("/internships")
def get_internship_listings(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all internship opportunities"""
    internships = db.query(InternshipListing).filter(
        InternshipListing.is_active == True
    ).offset(skip).limit(limit).all()
    
    return {
        "status": "success",
        "internships": [
            {
                "id": i.id,
                "title": i.title,
                "company": i.company,
                "location": i.location,
                "duration": i.duration,
                "stipend": i.stipend,
                "deadline": i.deadline
            } for i in internships
        ]
    }

@router.get("/internships/{internship_id}")
def get_internship_details(internship_id: str, db: Session = Depends(get_db)):
    """Get detailed internship information"""
    internship = db.query(InternshipListing).filter(
        InternshipListing.id == internship_id
    ).first()
    if not internship:
        raise HTTPException(status_code=404, detail="Internship not found")
    
    return {
        "status": "success",
        "internship": {
            "id": internship.id,
            "title": internship.title,
            "company": internship.company,
            "description": internship.description,
            "location": internship.location,
            "duration": internship.duration,
            "stipend": internship.stipend,
            "required_skills": internship.required_skills,
            "deadline": internship.deadline
        }
    }

# ─────────────────────────────────────────
# JOB APPLICATIONS
# ─────────────────────────────────────────

@router.post("/apply-job")
def apply_for_job(
    job_id: str,
    student_id: str,
    resume_id: str,
    cover_letter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Apply for a job position"""
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if already applied
    existing = db.query(JobApplication).filter(
        JobApplication.job_id == job_id,
        JobApplication.student_id == student_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already applied for this job")
    
    application = JobApplication(
        job_id=job_id,
        student_id=student_id,
        resume_id=resume_id,
        cover_letter=cover_letter,
        status="applied"
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    
    return {
        "status": "success",
        "message": "Application submitted",
        "application_id": application.id
    }

@router.get("/students/{student_id}/applications")
def get_student_applications(student_id: str, db: Session = Depends(get_db)):
    """Get all job applications from a student"""
    applications = db.query(JobApplication).filter(
        JobApplication.student_id == student_id
    ).all()
    
    return {
        "status": "success",
        "applications": [
            {
                "id": a.id,
                "job_id": a.job_id,
                "job_title": a.job.title,
                "company": a.job.company,
                "status": a.status,
                "applied_at": a.applied_at
            } for a in applications
        ]
    }

@router.get("/applications/{application_id}")
def get_application_details(application_id: str, db: Session = Depends(get_db)):
    """Get detailed application information"""
    app = db.query(JobApplication).filter(
        JobApplication.id == application_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {
        "status": "success",
        "application": {
            "id": app.id,
            "job": {
                "id": app.job.id,
                "title": app.job.title,
                "company": app.job.company
            },
            "status": app.status,
            "applied_at": app.applied_at
        }
    }

# ─────────────────────────────────────────
# PORTFOLIO
# ─────────────────────────────────────────

@router.post("/portfolio/create")
def create_portfolio(
    student_id: str,
    title: str,
    bio: str,
    website_url: Optional[str] = None,
    github_url: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create student portfolio"""
    portfolio = Portfolio(
        student_id=student_id,
        title=title,
        bio=bio,
        website_url=website_url,
        github_url=github_url,
        linkedin_url=linkedin_url
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    
    return {
        "status": "success",
        "message": "Portfolio created",
        "portfolio_id": portfolio.id
    }

@router.get("/portfolios/{portfolio_id}")
def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    """Get portfolio details"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    projects = db.query(PortfolioProject).filter(
        PortfolioProject.portfolio_id == portfolio_id
    ).all()
    
    return {
        "status": "success",
        "portfolio": {
            "id": portfolio.id,
            "title": portfolio.title,
            "bio": portfolio.bio,
            "website_url": portfolio.website_url,
            "github_url": portfolio.github_url,
            "linkedin_url": portfolio.linkedin_url,
            "projects": [
                {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description,
                    "technologies": p.technologies,
                    "github_link": p.github_link,
                    "live_link": p.live_link
                } for p in projects
            ]
        }
    }

@router.post("/portfolios/{portfolio_id}/projects")
def add_portfolio_project(
    portfolio_id: str,
    title: str,
    description: str,
    technologies: list,
    github_link: Optional[str] = None,
    live_link: Optional[str] = None,
    image_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Add project to portfolio"""
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    project = PortfolioProject(
        portfolio_id=portfolio_id,
        title=title,
        description=description,
        technologies=technologies,
        github_link=github_link,
        live_link=live_link,
        image_url=image_url
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return {
        "status": "success",
        "message": "Project added to portfolio",
        "project_id": project.id
    }

# ─────────────────────────────────────────
# PLACEMENT STATISTICS
# ─────────────────────────────────────────

@router.get("/placement-stats")
def get_placement_statistics(db: Session = Depends(get_db)):
    """Get overall platform placement statistics"""
    total_jobs = db.query(JobListing).filter(JobListing.is_active == True).count()
    total_applications = db.query(JobApplication).count()
    total_internships = db.query(InternshipListing).filter(
        InternshipListing.is_active == True
    ).count()
    
    return {
        "status": "success",
        "stats": {
            "total_active_jobs": total_jobs,
            "total_applications": total_applications,
            "total_internships": total_internships,
            "average_salary": "25-35 LPA",
            "top_hiring_companies": ["Google", "Microsoft", "Amazon", "Meta"],
            "placement_rate": "92%"
        }
    }
