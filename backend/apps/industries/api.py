"""Industry management API."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Industry

router = APIRouter(prefix="/industries", tags=["行业配置"])


class IndustryCreate(BaseModel):
    name: str
    keywords: List[str] = []
    enabled: bool = True


class IndustryUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[List[str]] = None
    enabled: Optional[bool] = None


class IndustryResponse(BaseModel):
    id: int
    name: str
    keywords: List[str]
    enabled: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=List[IndustryResponse])
def get_industries(db: Session = Depends(get_db)):
    """Get all industries."""
    industries = db.query(Industry).order_by(Industry.created_at.desc()).all()
    return industries


@router.post("/", response_model=IndustryResponse)
def create_industry(industry: IndustryCreate, db: Session = Depends(get_db)):
    """Create a new industry."""
    existing = db.query(Industry).filter(Industry.name == industry.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="行业名称已存在")

    db_industry = Industry(
        name=industry.name,
        keywords=industry.keywords,
        enabled=industry.enabled
    )
    db.add(db_industry)
    db.commit()
    db.refresh(db_industry)
    return db_industry


@router.get("/{industry_id}", response_model=IndustryResponse)
def get_industry(industry_id: int, db: Session = Depends(get_db)):
    """Get industry by ID."""
    industry = db.query(Industry).filter(Industry.id == industry_id).first()
    if not industry:
        raise HTTPException(status_code=404, detail="行业不存在")
    return industry


@router.put("/{industry_id}", response_model=IndustryResponse)
def update_industry(
    industry_id: int,
    industry: IndustryUpdate,
    db: Session = Depends(get_db)
):
    """Update industry."""
    db_industry = db.query(Industry).filter(Industry.id == industry_id).first()
    if not db_industry:
        raise HTTPException(status_code=404, detail="行业不存在")

    update_data = industry.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_industry, key, value)

    db.commit()
    db.refresh(db_industry)
    return db_industry


@router.delete("/{industry_id}")
def delete_industry(industry_id: int, db: Session = Depends(get_db)):
    """Delete industry."""
    industry = db.query(Industry).filter(Industry.id == industry_id).first()
    if not industry:
        raise HTTPException(status_code=404, detail="行业不存在")

    db.delete(industry)
    db.commit()
    return {"message": "删除成功"}
