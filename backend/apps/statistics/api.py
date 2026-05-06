"""Statistics API routes."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from apps.statistics.service import StatisticsService

router = APIRouter(prefix="/statistics", tags=["统计分析"])


@router.get("/overview")
def get_overview_stats(db: Session = Depends(get_db)):
    """Get overall system statistics overview."""
    service = StatisticsService(db)
    return service.get_overview_stats()


@router.get("/earthquake")
def get_earthquake_stats(
    period: str = Query("monthly", regex="^(daily|weekly|monthly|yearly)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_magnitude: float = Query(4.0, ge=0),
    region: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get earthquake activity statistics."""
    service = StatisticsService(db)
    return service.get_earthquake_stats(
        period=period,
        start_date=start_date,
        end_date=end_date,
        min_magnitude=min_magnitude,
        region=region
    )


@router.get("/academic")
def get_academic_stats(
    start_year: int = Query(2020, ge=2000),
    end_year: int = Query(2026, le=2030),
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get academic research statistics."""
    service = StatisticsService(db)
    return service.get_academic_stats(
        start_year=start_year,
        end_year=end_year,
        source=source
    )


@router.get("/crawl")
def get_crawl_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get crawler performance statistics."""
    service = StatisticsService(db)
    return service.get_crawl_stats(days=days)
