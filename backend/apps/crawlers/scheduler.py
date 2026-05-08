"""Crawler scheduler service."""
import asyncio
import logging
import threading
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.models import DataSource, CrawlLog, CrawlStatus, EarthquakeEvent
from apps.crawlers.registry import init_registry, get_spider, SpiderConfig
from apps.crawlers.earthquake_service import EarthquakeService
from apps.articles.service import ArticleService

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


class CrawlerScheduler:
    """Crawler scheduler service."""

    def __init__(self):
        init_registry()
        self.scheduler = scheduler

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Crawler scheduler started")
            self._schedule_all_sources()

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Crawler scheduler stopped")

    def _schedule_all_sources(self):
        """Schedule all enabled data sources."""
        db = SessionLocal()
        try:
            sources = db.query(DataSource).filter(DataSource.enabled == True).all()
            for source in sources:
                self._schedule_source(source)
            logger.info(f"Scheduled {len(sources)} data sources")
        finally:
            db.close()

    def _schedule_source(self, source: DataSource):
        """Schedule a single data source."""
        job_id = f"crawl_{source.id}"

        existing_job = self.scheduler.get_job(job_id)
        if existing_job:
            self.scheduler.remove_job(job_id)

        self.scheduler.add_job(
            self._run_crawler,
            trigger=IntervalTrigger(seconds=source.update_interval),
            args=[source.id],
            id=job_id,
            replace_existing=True,
            max_instances=1
        )
        logger.info(f"Scheduled source: {source.name} (interval: {source.update_interval}s)")

    async def _run_crawler(self, source_id: int):
        """Run crawler for a specific source."""
        db = SessionLocal()
        log = CrawlLog(
            source_id=source_id,
            started_at=datetime.utcnow(),
            status=CrawlStatus.SUCCESS
        )

        try:
            source = db.query(DataSource).filter(DataSource.id == source_id).first()
            if not source or not source.enabled:
                logger.warning(f"Source {source_id} not found or disabled")
                return

            spider = get_spider(source.spider_class, SpiderConfig(
                keywords=source.keywords or [],
                rate_limit=source.rate_limit,
                update_interval=source.update_interval
            ))

            if not spider:
                raise ValueError(f"Spider class {source.spider_class} not found")

            logger.info(f"Starting crawl for: {source.name}")

            async with spider:
                results = await spider.crawl()

            article_count = 0
            event_count = 0

            # Collect all event IDs that will be added to avoid duplicates within this batch
            seen_events = set()

            for item in results:
                if hasattr(item, 'magnitude') and hasattr(item, 'latitude'):
                    from apps.crawlers.base import EarthquakeEventData
                    if isinstance(item, EarthquakeEventData):
                        # Create a unique key for this event
                        event_key = (item.event_id, item.source)

                        # Skip if already processed in this batch
                        if event_key in seen_events:
                            continue
                        seen_events.add(event_key)

                        # Check if event already exists in database
                        existing = db.query(EarthquakeEvent).filter(
                            EarthquakeEvent.event_id == item.event_id,
                            EarthquakeEvent.source == item.source
                        ).first()

                        if existing:
                            # Update existing event
                            existing.magnitude = item.magnitude
                            existing.latitude = item.latitude
                            existing.longitude = item.longitude
                            existing.depth = item.depth
                            existing.location = item.location
                            existing.region = item.region
                            existing.time = item.time
                        else:
                            # Create new event
                            event = EarthquakeEvent(
                                event_id=item.event_id,
                                magnitude=item.magnitude,
                                latitude=item.latitude,
                                longitude=item.longitude,
                                depth=item.depth,
                                location=item.location,
                                region=item.region,
                                time=item.time,
                                source=item.source
                            )
                            db.add(event)
                            event_count += 1
                elif hasattr(item, 'title') and hasattr(item, 'summary'):
                    from apps.crawlers.base import Article
                    if isinstance(item, Article):
                        article_service = ArticleService(db)
                        # Truncate author to fit database column limit
                        author = item.author[:500] if item.author and len(item.author) > 500 else item.author
                        article_service.create_article(
                            title=item.title[:1000] if item.title and len(item.title) > 1000 else item.title,
                            content=item.content or item.summary or "",
                            summary=(item.content or item.summary or "")[:2000][:500],
                            url=item.url,
                            source=item.source or source.name,
                            author=author,
                            published_at=item.published_at,
                            industry_id=source.industry_id
                        )
                        article_count += 1

            source.last_crawl_at = datetime.utcnow()
            log.articles_count = article_count + event_count
            log.status = CrawlStatus.SUCCESS
            log.completed_at = datetime.utcnow()

            db.add(log)
            db.commit()

            logger.info(f"Crawl completed for {source.name}: {article_count} articles, {event_count} events")

        except Exception as e:
            logger.error(f"Crawl failed for source {source_id}: {e}")
            log.status = CrawlStatus.FAILED
            log.error_message = str(e)
            log.completed_at = datetime.utcnow()
            db.add(log)
            db.commit()

        finally:
            db.close()

    def crawl_now(self, source_id: int):
        """Trigger immediate crawl for a source."""
        # Schedule immediate execution
        self.scheduler.add_job(
            self._run_crawler_sync,
            trigger=None,
            args=[source_id],
            id=f"crawl_now_{source_id}",
            replace_existing=True
        )
        logger.info(f"Scheduled immediate crawl for source {source_id}")

    def _run_crawler_sync(self, source_id: int):
        """Synchronous wrapper to run async crawler."""
        asyncio.run(self._run_crawler(source_id))

    def add_source(self, source_id: int):
        """Add a new source to the scheduler."""
        db = SessionLocal()
        try:
            source = db.query(DataSource).filter(DataSource.id == source_id).first()
            if source and source.enabled:
                self._schedule_source(source)
        finally:
            db.close()

    def remove_source(self, source_id: int):
        """Remove a source from the scheduler."""
        job_id = f"crawl_{source_id}"
        job = self.scheduler.get_job(job_id)
        if job:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed source {source_id} from scheduler")

    def pause_source(self, source_id: int):
        """Pause a source crawler."""
        job_id = f"crawl_{source_id}"
        self.scheduler.pause_job(job_id)

    def resume_source(self, source_id: int):
        """Resume a source crawler."""
        job_id = f"crawl_{source_id}"
        self.scheduler.resume_job(job_id)


crawler_scheduler = CrawlerScheduler()
