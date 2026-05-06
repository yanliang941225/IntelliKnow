"""Base spider class for all crawlers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import httpx
import logging

logger = logging.getLogger(__name__)


@dataclass
class SpiderConfig:
    """Spider configuration."""
    keywords: List[str] = field(default_factory=list)
    update_interval: int = 3600
    rate_limit: int = 10
    max_results: int = 100
    timeout: int = 30
    max_retries: int = 3


@dataclass
class Article:
    """Article data model."""
    title: str
    content: str = ""
    summary: str = ""
    url: str = ""
    source: str = ""
    author: str = ""
    published_at: Optional[datetime] = None
    keywords: List[str] = field(default_factory=list)
    extra_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EarthquakeEventData:
    """Earthquake event data model."""
    event_id: str
    magnitude: float
    latitude: float
    longitude: float
    depth: float
    location: str
    region: str = ""
    time: Optional[datetime] = None
    source: str = ""


class BaseSpider(ABC):
    """Base class for all spiders."""

    def __init__(self, config: SpiderConfig):
        self.config = config
        self.name = self.__class__.__name__
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            follow_redirects=True  # 跟随 HTTP 重定向
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    @abstractmethod
    async def search(self, query: str) -> List[Article]:
        """Search and return article list."""
        pass

    @abstractmethod
    async def fetch_article(self, article_id: str) -> Optional[Article]:
        """Fetch single article details."""
        pass

    async def crawl(self) -> List[Article]:
        """Execute crawl process."""
        results = []
        
        # If no keywords configured, do a single crawl without keyword filtering
        if not self.config.keywords:
            try:
                articles = await self.search("")
                results.extend(articles)
                logger.info(f"[{self.name}] Fetched {len(articles)} articles (no keywords)")
            except Exception as e:
                logger.error(f"[{self.name}] Error during crawl: {e}")
            return results
        
        for keyword in self.config.keywords:
            try:
                articles = await self.search(keyword)
                results.extend(articles)
                logger.info(f"[{self.name}] Fetched {len(articles)} articles for keyword: {keyword}")
            except Exception as e:
                logger.error(f"[{self.name}] Error fetching keyword '{keyword}': {e}")
            finally:
                await self._rate_limit()
        return results

    async def _rate_limit(self):
        """Rate limiting."""
        await asyncio.sleep(self.config.rate_limit)

    async def _fetch_with_retry(self, url: str, **kwargs) -> Optional[httpx.Response]:
        """Fetch URL with retry logic."""
        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.get(url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPError as e:
                logger.warning(f"[{self.name}] Attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        return None

    def parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse datetime string."""
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
