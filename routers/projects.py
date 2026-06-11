from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import models
from database import get_db
from auth_utils import get_current_user

router = APIRouter()

class ProjectCreate(BaseModel):
    title: str
    domain: str
    level: str
    description: str
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    tutorial_url: Optional[str] = None
    tags: List[str] = []

@router.get("/")
def list_projects(domain: Optional[str] = None, level: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.ProjectCatalog)
    if domain:
        query = query.filter(models.ProjectCatalog.domain.ilike(f"%{domain}%"))
    if level:
        query = query.filter(models.ProjectCatalog.level.ilike(f"%{level}%"))
    return query.all()

@router.post("/")
def create_project(data: ProjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role not in ["faculty", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    project = models.ProjectCatalog(
        title=data.title,
        domain=data.domain,
        level=data.level,
        description=data.description,
        github_url=data.github_url,
        live_url=data.live_url,
        tutorial_url=data.tutorial_url,
        tags=data.tags
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/{project_id}/playlist")
def get_project_playlist(project_id: str, db: Session = Depends(get_db)):
    return db.query(models.ProjectPlaylist).filter(models.ProjectPlaylist.project_id == project_id).order_by(models.ProjectPlaylist.order_index).all()
