"""News spider for emergency management."""
import httpx
import feedparser
from datetime import datetime
from typing import List, Optional
from apps.crawlers.base import BaseSpider, SpiderConfig, Article
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class EmergencyNewsSpider(BaseSpider):
    """Emergency Management Ministry News Spider."""

    def __init__(self, config: SpiderConfig = None):
        super().__init__(config or SpiderConfig())
        self.base_url = "https://www.mem.gov.cn/xw/zhsgxx/"
        self.rss_feeds = [
            "http://www.cneb.gov.cn/dzsb/",
        ]

    async def _fetch_with_retry(self, url: str, **kwargs) -> Optional[httpx.Response]:
        """Fetch URL with retry logic and compression handling."""
        for attempt in range(self.config.max_retries):
            try:
                async with httpx.AsyncClient(
                    timeout=self.config.timeout,
                    follow_redirects=True,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    }
                ) as client:
                    response = await client.get(url, **kwargs)
                    response.raise_for_status()
                    return response
            except httpx.HTTPError as e:
                logger.warning(f"[EmergencyNewsSpider] Attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
        return None

    async def search(self, query: str = "") -> List[Article]:
        """Fetch news from Emergency Management Ministry."""
        articles = []

        try:
            response = await self._fetch_with_retry(self.base_url)
            if response:
                soup = BeautifulSoup(response.text, "lxml")

                # Try different selectors
                news_items = []
                for selector in [".list_list02 li", ".news_list li", ".list-item", ".xwzx-list li", "ul li"]:
                    items = soup.select(selector)
                    if items:
                        news_items = items
                        break

                for item in news_items[:self.config.max_results]:
                    try:
                        title_elem = item.select_one("a")
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        if not title:
                            continue

                        link = title_elem.get("href", "")

                        if link and not link.startswith("http"):
                            if link.startswith("/"):
                                link = "https://www.mem.gov.cn" + link
                            else:
                                link = "https://www.mem.gov.cn/xw/zhsgxx/" + link

                        # Try to find date
                        date_elem = item.select_one(".date, .time, span")
                        date_str = date_elem.get_text(strip=True) if date_elem else ""

                        article = Article(
                            title=title[:500] if title else "",
                            summary=f"来源: 应急管理部 | {date_str}" if date_str else "来源: 应急管理部",
                            url=link if link else self.base_url,
                            source="应急管理部",
                            published_at=self._parse_chinese_date(date_str),
                        )
                        articles.append(article)
                    except Exception as e:
                        logger.debug(f"Error parsing news item: {e}")
                        continue

            logger.info(f"[EmergencyNewsSpider] Fetched {len(articles)} news from MEM")
        except Exception as e:
            logger.error(f"[EmergencyNewsSpider] Error: {e}")

        return articles

    async def fetch_article(self, article_id: str) -> Optional[Article]:
        """Fetch single article content."""
        url = article_id
        try:
            response = await self._fetch_with_retry(url)
            if not response:
                return None

            soup = BeautifulSoup(response.text, "lxml")

            title_elem = soup.select_one("h1, .article-title, .title")
            title = title_elem.get_text(strip=True) if title_elem else ""
            content_div = soup.select_one(".article-content, .content, #article-content")
            content = content_div.get_text(strip=True) if content_div else ""

            date_elem = soup.select_one(".date, .time, .article-date")
            date_str = date_elem.get_text(strip=True) if date_elem else ""

            return Article(
                title=title[:500] if title else "",
                content=content[:5000] if content else "",
                summary=content[:500] if content else "",
                url=url,
                source="应急管理部",
                published_at=self._parse_chinese_date(date_str),
            )

        except Exception as e:
            logger.error(f"[EmergencyNewsSpider] Error fetching article: {e}")
            return None

    def _parse_chinese_date(self, date_str: str) -> Optional[datetime]:
        """Parse Chinese date format like '2024-01-15' or '2024年01月15日'."""
        if not date_str:
            return None

        patterns = [
            (r"(\d{4})-(\d{1,2})-(\d{1,2})", "%Y-%m-%d"),
            (r"(\d{4})年(\d{1,2})月(\d{1,2})日", "%Y年%m月%d日"),
            (r"(\d{4})/(\d{1,2})/(\d{1,2})", "%Y/%m/%d"),
        ]

        for pattern, fmt in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if "年" in fmt:
                        return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                    else:
                        return datetime.strptime(f"{match.group(1)}-{match.group(2)}-{match.group(3)}", fmt)
                except ValueError:
                    continue

        return None


class RSSNewsSpider(BaseSpider):
    """Generic RSS Feed Spider."""

    def __init__(self, config: SpiderConfig = None):
        super().__init__(config or SpiderConfig())
        self.feed_urls = []

    def add_feed(self, url: str):
        """Add RSS feed URL."""
        self.feed_urls.append(url)

    async def search(self, query: str = "") -> List[Article]:
        """Fetch news from RSS feeds."""
        articles = []

        for feed_url in self.feed_urls:
            try:
                response = await self._fetch_with_retry(feed_url)
                if not response:
                    continue

                feed = feedparser.parse(response.text)

                for entry in feed.entries[:self.config.max_results]:
                    article = Article(
                        title=entry.get("title", ""),
                        content=entry.get("summary", "") or entry.get("description", ""),
                        summary=entry.get("summary", "")[:500] if entry.get("summary") else "",
                        url=entry.get("link", ""),
                        source=feed.feed.get("title", feed_url),
                        author=entry.get("author", ""),
                        published_at=self.parse_datetime(entry.get("published", "")) if entry.get("published") else None,
                    )
                    articles.append(article)

                logger.info(f"[RSSNewsSpider] Fetched {len(feed.entries)} items from {feed_url}")

            except Exception as e:
                logger.error(f"[RSSNewsSpider] Error fetching {feed_url}: {e}")
                continue

        return articles

    async def fetch_article(self, article_id: str) -> Optional[Article]:
        """Fetch single article content."""
        return None
