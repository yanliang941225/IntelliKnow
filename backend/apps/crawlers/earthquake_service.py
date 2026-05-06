"""Earthquake event service."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from core.models import EarthquakeEvent


class EarthquakeService:
    """Earthquake event service."""

    def __init__(self, db: Session):
        self.db = db

    def create_event(
        self,
        event_id: str,
        magnitude: float,
        latitude: float,
        longitude: float,
        depth: float,
        location: str,
        region: str = "",
        time: datetime = None,
        source: str = ""
    ) -> EarthquakeEvent:
        """Create or update earthquake event."""
        existing = self.db.query(EarthquakeEvent).filter(
            EarthquakeEvent.event_id == event_id,
            EarthquakeEvent.source == source
        ).first()

        if existing:
            existing.magnitude = magnitude
            existing.latitude = latitude
            existing.longitude = longitude
            existing.depth = depth
            existing.location = location
            existing.region = region
            existing.time = time
            self.db.commit()
            self.db.refresh(existing)
            return existing

        event = EarthquakeEvent(
            event_id=event_id,
            magnitude=magnitude,
            latitude=latitude,
            longitude=longitude,
            depth=depth,
            location=location,
            region=region,
            time=time,
            source=source
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def bulk_create_events(self, events: List[EarthquakeEvent]) -> int:
        """Bulk create earthquake events."""
        count = 0
        for event_data in events:
            existing = self.db.query(EarthquakeEvent).filter(
                EarthquakeEvent.event_id == event_data.event_id,
                EarthquakeEvent.source == event_data.source
            ).first()

            if not existing:
                self.db.add(event_data)
                count += 1

        self.db.commit()
        return count

    def get_event(self, event_id: int) -> Optional[EarthquakeEvent]:
        """Get earthquake event by ID."""
        return self.db.query(EarthquakeEvent).filter(
            EarthquakeEvent.id == event_id
        ).first()

    def get_events(
        self,
        min_magnitude: float = 0,
        max_magnitude: float = None,
        min_latitude: float = None,
        max_latitude: float = None,
        min_longitude: float = None,
        max_longitude: float = None,
        region: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        source: str = None,
        page: int = 1,
        page_size: int = 50
    ) -> List[EarthquakeEvent]:
        """Get earthquake events with filters."""
        query = self.db.query(EarthquakeEvent)

        if min_magnitude > 0:
            query = query.filter(EarthquakeEvent.magnitude >= min_magnitude)
        if max_magnitude:
            query = query.filter(EarthquakeEvent.magnitude <= max_magnitude)
        if min_latitude is not None:
            query = query.filter(EarthquakeEvent.latitude >= min_latitude)
        if max_latitude is not None:
            query = query.filter(EarthquakeEvent.latitude <= max_latitude)
        if min_longitude is not None:
            query = query.filter(EarthquakeEvent.longitude >= min_longitude)
        if max_longitude is not None:
            query = query.filter(EarthquakeEvent.longitude <= max_longitude)
        if region:
            query = query.filter(EarthquakeEvent.region.like(f"%{region}%"))
        if start_time:
            query = query.filter(EarthquakeEvent.time >= start_time)
        if end_time:
            query = query.filter(EarthquakeEvent.time <= end_time)
        if source:
            query = query.filter(EarthquakeEvent.source == source)

        query = query.order_by(desc(EarthquakeEvent.time))

        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size).all()

    def count_events(
        self,
        min_magnitude: float = 0,
        region: str = None,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> int:
        """Count earthquake events with filters."""
        query = self.db.query(EarthquakeEvent)

        if min_magnitude > 0:
            query = query.filter(EarthquakeEvent.magnitude >= min_magnitude)
        if region:
            query = query.filter(EarthquakeEvent.region.like(f"%{region}%"))
        if start_time:
            query = query.filter(EarthquakeEvent.time >= start_time)
        if end_time:
            query = query.filter(EarthquakeEvent.time <= end_time)

        return query.count()

    def get_recent_events(self, limit: int = 10) -> List[EarthquakeEvent]:
        """Get recent earthquake events."""
        return self.db.query(EarthquakeEvent).order_by(
            desc(EarthquakeEvent.time)
        ).limit(limit).all()

    def get_major_events(self, min_magnitude: float = 6.0, limit: int = 10) -> List[EarthquakeEvent]:
        """Get major earthquake events."""
        return self.db.query(EarthquakeEvent).filter(
            EarthquakeEvent.magnitude >= min_magnitude
        ).order_by(desc(EarthquakeEvent.time)).limit(limit).all()
