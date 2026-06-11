from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import models
from database import get_db
from auth_utils import get_current_user

router = APIRouter()

class ResourceCreate(BaseModel):
    title: str
    domain: str
    url: Optional[str] = None
    resource_type: str
    description: str

@router.get("/")
def list_resources(domain: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.ResourceHub)
    if domain:
        query = query.filter(models.ResourceHub.domain.ilike(f"%{domain}%"))
    return query.all()

@router.post("/")
def create_resource(data: ResourceCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role not in ["faculty", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    resource = models.ResourceHub(
        title=data.title,
        domain=data.domain,
        url=data.url,
        resource_type=data.resource_type,
        description=data.description,
        created_by=current_user.id
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource
