"""Earthquake API routes."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from apps.crawlers.earthquake_service import EarthquakeService

router = APIRouter(prefix="/earthquakes", tags=["地震事件"])


@router.get("/")
def get_earthquakes(
    min_magnitude: float = Query(4.0, ge=0),
    max_magnitude: Optional[float] = None,
    region: Optional[str] = None,
    source: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get earthquake events with filters."""
    service = EarthquakeService(db)

    events = service.get_events(
        min_magnitude=min_magnitude,
        max_magnitude=max_magnitude,
        region=region,
        source=source,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )

    total = service.count_events(
        min_magnitude=min_magnitude,
        region=region,
        start_time=start_time,
        end_time=end_time
    )

    return {
        "items": events,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{event_id}")
def get_earthquake(event_id: int, db: Session = Depends(get_db)):
    """Get earthquake event by ID."""
    service = EarthquakeService(db)
    event = service.get_event(event_id)

    if not event:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="地震事件不存在")

    return event


@router.get("/recent/list")
def get_recent_earthquakes(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get recent earthquake events."""
    service = EarthquakeService(db)
    return service.get_recent_events(limit=limit)


@router.get("/major/list")
def get_major_earthquakes(
    min_magnitude: float = Query(6.0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get major earthquake events."""
    service = EarthquakeService(db)
    return service.get_major_events(min_magnitude=min_magnitude, limit=limit)
