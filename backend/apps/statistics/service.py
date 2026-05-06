"""Statistics service for earthquake industry analysis."""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from collections import Counter
import logging

from core.models import EarthquakeEvent, Article, Statistics, CrawlLog

logger = logging.getLogger(__name__)


class StatisticsService:
    """Statistics analysis service for earthquake industry."""

    def __init__(self, db: Session):
        self.db = db

    def get_earthquake_stats(
        self,
        period: str = "monthly",
        start_date: datetime = None,
        end_date: datetime = None,
        min_magnitude: float = 4.0,
        region: str = None
    ) -> Dict[str, Any]:
        """Get earthquake activity statistics."""
        if not start_date:
            if period == "daily":
                start_date = datetime.utcnow() - timedelta(days=7)
            elif period == "weekly":
                start_date = datetime.utcnow() - timedelta(weeks=4)
            elif period == "monthly":
                start_date = datetime.utcnow() - timedelta(days=365)
            else:
                start_date = datetime.utcnow() - timedelta(days=365 * 2)

        if not end_date:
            end_date = datetime.utcnow()

        query = self.db.query(EarthquakeEvent).filter(
            and_(
                EarthquakeEvent.time >= start_date,
                EarthquakeEvent.time <= end_date,
                EarthquakeEvent.magnitude >= min_magnitude
            )
        )

        if region:
            query = query.filter(EarthquakeEvent.region.like(f"%{region}%"))

        events = query.all()

        total_count = len(events)
        by_magnitude = self._count_by_magnitude(events)
        by_depth = self._count_by_depth(events)
        by_region = self._count_by_region(events)
        by_source = self._count_by_source(events)
        trend = self._get_time_trend(events, period)

        return {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_count": total_count,
            "min_magnitude": min_magnitude,
            "by_magnitude": by_magnitude,
            "by_depth": by_depth,
            "by_region": by_region[:20],
            "by_source": by_source,
            "trend": trend,
            "summary": {
                "max_magnitude": max([e.magnitude for e in events]) if events else 0,
                "avg_magnitude": sum([e.magnitude for e in events]) / total_count if total_count > 0 else 0,
                "max_depth": max([e.depth for e in events]) if events else 0,
                "avg_depth": sum([e.depth for e in events]) / total_count if total_count > 0 else 0,
            }
        }

    def _count_by_magnitude(self, events: List[EarthquakeEvent]) -> Dict[str, int]:
        """Count events by magnitude ranges."""
        counts = {"M4.0-4.9": 0, "M5.0-5.9": 0, "M6.0-6.9": 0, "M7.0-7.9": 0, "M8.0+": 0}
        for e in events:
            mag = e.magnitude
            if mag >= 8.0:
                counts["M8.0+"] += 1
            elif mag >= 7.0:
                counts["M7.0-7.9"] += 1
            elif mag >= 6.0:
                counts["M6.0-6.9"] += 1
            elif mag >= 5.0:
                counts["M5.0-5.9"] += 1
            else:
                counts["M4.0-4.9"] += 1
        return counts

    def _count_by_depth(self, events: List[EarthquakeEvent]) -> Dict[str, int]:
        """Count events by depth ranges."""
        counts = {"浅源 (<70km)": 0, "中源 (70-300km)": 0, "深源 (>300km)": 0}
        for e in events:
            depth = e.depth or 0
            if depth < 70:
                counts["浅源 (<70km)"] += 1
            elif depth <= 300:
                counts["中源 (70-300km)"] += 1
            else:
                counts["深源 (>300km)"] += 1
        return counts

    def _count_by_region(self, events: List[EarthquakeEvent]) -> List[Dict[str, Any]]:
        """Count events by region."""
        regions = [e.region or e.location.split(",")[-1].strip() if e.location else "Unknown" for e in events]
        counter = Counter(regions)
        return [{"region": r, "count": c} for r, c in counter.most_common(20)]

    def _count_by_source(self, events: List[EarthquakeEvent]) -> Dict[str, int]:
        """Count events by data source."""
        sources = [e.source for e in events]
        return dict(Counter(sources))

    def _get_time_trend(
        self,
        events: List[EarthquakeEvent],
        period: str
    ) -> List[Dict[str, Any]]:
        """Get time series trend of earthquake events."""
        trend = {}

        for e in events:
            if not e.time:
                continue

            if period == "daily":
                key = e.time.strftime("%Y-%m-%d")
            elif period == "weekly":
                key = e.time.strftime("%Y-W%W")
            elif period == "monthly":
                key = e.time.strftime("%Y-%m")
            else:
                key = e.time.strftime("%Y")

            if key not in trend:
                trend[key] = {"period": key, "count": 0, "total_magnitude": 0, "max_magnitude": 0}

            trend[key]["count"] += 1
            trend[key]["total_magnitude"] += e.magnitude or 0
            trend[key]["max_magnitude"] = max(trend[key]["max_magnitude"], e.magnitude or 0)

        for item in trend.values():
            item["avg_magnitude"] = round(item["total_magnitude"] / item["count"], 2) if item["count"] > 0 else 0

        result = sorted(trend.values(), key=lambda x: x["period"])
        return result

    def get_academic_stats(
        self,
        start_year: int = 2020,
        end_year: int = 2026,
        source: str = None
    ) -> Dict[str, Any]:
        """Get academic research statistics."""
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31, 23, 59, 59)

        query = self.db.query(Article).filter(
            and_(
                Article.published_at >= start_date,
                Article.published_at <= end_date,
                Article.source.in_(["arXiv", "Semantic Scholar", "OpenAlex"])
            )
        )

        if source:
            query = query.filter(Article.source == source)

        articles = query.all()

        total_papers = len(articles)
        by_source = self._count_articles_by_source(articles)
        monthly_trend = self._get_article_trend(articles)
        top_sources = self._get_top_sources(articles, limit=10)

        return {
            "start_year": start_year,
            "end_year": end_year,
            "total_papers": total_papers,
            "by_source": by_source,
            "monthly_trend": monthly_trend,
            "top_sources": top_sources,
        }

    def _count_articles_by_source(self, articles: List[Article]) -> Dict[str, int]:
        """Count articles by source."""
        sources = [a.source for a in articles if a.source]
        return dict(Counter(sources))

    def _get_article_trend(self, articles: List[Article]) -> List[Dict[str, Any]]:
        """Get monthly article publication trend."""
        trend = {}

        for a in articles:
            if not a.published_at:
                continue

            key = a.published_at.strftime("%Y-%m")
            if key not in trend:
                trend[key] = {"period": key, "count": 0}

            trend[key]["count"] += 1

        result = sorted(trend.values(), key=lambda x: x["period"])
        return result

    def _get_top_sources(self, articles: List[Article], limit: int = 10) -> List[Dict[str, Any]]:
        """Get top article sources."""
        source_counts = Counter([a.source for a in articles if a.source])
        return [{"source": s, "count": c} for s, c in source_counts.most_common(limit)]

    def get_crawl_stats(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get crawler performance statistics."""
        start_date = datetime.utcnow() - timedelta(days=days)

        logs = self.db.query(CrawlLog).filter(
            CrawlLog.started_at >= start_date
        ).order_by(desc(CrawlLog.started_at)).all()

        total_runs = len(logs)
        success_count = sum(1 for log in logs if log.status.value == "success")
        failed_count = sum(1 for log in logs if log.status.value == "failed")

        total_articles = sum(log.articles_count or 0 for log in logs)

        by_source = {}
        for log in logs:
            source_name = log.data_source.name if log.data_source else "Unknown"
            if source_name not in by_source:
                by_source[source_name] = {"runs": 0, "success": 0, "articles": 0}
            by_source[source_name]["runs"] += 1
            if log.status.value == "success":
                by_source[source_name]["success"] += 1
            by_source[source_name]["articles"] += log.articles_count or 0

        return {
            "period_days": days,
            "total_runs": total_runs,
            "success_rate": round(success_count / total_runs * 100, 2) if total_runs > 0 else 0,
            "total_articles": total_articles,
            "by_source": by_source
        }

    def get_overview_stats(self) -> Dict[str, Any]:
        """Get overall system statistics overview."""
        earthquake_count = self.db.query(EarthquakeEvent).count()
        article_count = self.db.query(Article).count()
        source_count = self.db.query(func.count(func.distinct(Article.source))).scalar() or 0

        week_ago = datetime.utcnow() - timedelta(days=7)

        # Get recent events for map (latest 50 events from last 7 days)
        recent_events = self.db.query(EarthquakeEvent).filter(
            EarthquakeEvent.time >= week_ago
        ).order_by(desc(EarthquakeEvent.time)).limit(50).all()

        recent_articles = self.db.query(Article).order_by(
            desc(Article.published_at)
        ).limit(10).all()

        return {
            "earthquake_count": earthquake_count,
            "article_count": article_count,
            "source_count": source_count,
            "recent_events": [
                {
                    "event_id": e.event_id,
                    "magnitude": e.magnitude,
                    "latitude": e.latitude,
                    "longitude": e.longitude,
                    "location": e.location,
                    "time": e.time.isoformat() if e.time else None,
                    "source": e.source,
                    "depth": e.depth,
                    "region": e.region
                }
                for e in recent_events
            ],
            "recent_articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "source": a.source,
                    "published_at": a.published_at.isoformat() if a.published_at else None
                }
                for a in recent_articles
            ]
        }
