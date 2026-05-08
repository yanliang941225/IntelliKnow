"""Academic paper spiders."""
import httpx
from datetime import datetime
from typing import List, Optional
from apps.crawlers.base import BaseSpider, SpiderConfig, Article
import logging
import feedparser
import re

logger = logging.getLogger(__name__)


class ArxivSeismologySpider(BaseSpider):
    """arXiv Seismology Papers Spider.

    Uses arXiv API to fetch papers from Earth and Planetary Sciences category.
    """

    def __init__(self, config: SpiderConfig = None):
        super().__init__(config or SpiderConfig())
        self.base_url = "https://export.arxiv.org/api/query"
        # 只搜索地球物理和地震学相关分类
        self.seismology_categories = ["physics.geo-ph"]

    async def search(self, query: str = "") -> List[Article]:
        """Search papers from arXiv within seismology categories."""
        keywords = query or " OR ".join(self.config.keywords[:3]) if self.config.keywords else "earthquake OR seismology OR seismic"
        max_results = min(self.config.max_results, 100)

        articles = []
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for category in self.seismology_categories:
            # 搜索时限定分类：cat:分类名 AND (关键词1 OR 关键词2)
            url = f"{self.base_url}?search_query=cat:{category}+AND+({keywords})&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"

            try:
                response = await self._fetch_with_retry(url)
                if not response:
                    continue

                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)

                for entry in root.findall("atom:entry", ns):
                    title = entry.find("atom:title", ns)
                    summary = entry.find("atom:summary", ns)
                    published = entry.find("atom:published", ns)
                    author_list = entry.findall("atom:author", ns)
                    link = entry.find("atom:id", ns)

                    authors = ", ".join([
                        author.find("atom:name", ns).text
                        for author in author_list
                        if author.find("atom:name", ns) is not None
                    ])

                    article = Article(
                        title=self._clean_text(title.text if title is not None else ""),
                        content=self._clean_text(summary.text if summary is not None else ""),
                        summary=self._clean_text(summary.text[:500] if summary is not None else ""),
                        url=link.text if link is not None else "",
                        source="arXiv",
                        author=authors,
                        published_at=self.parse_datetime(published.text if published is not None else ""),
                        keywords=[keywords]
                    )
                    articles.append(article)

                logger.info(f"[ArxivSpider] Fetched {len(articles)} papers from category {category}")

            except Exception as e:
                logger.error(f"[ArxivSpider] Error fetching category {category}: {e}")

        # 去重（同一论文可能出现在多个分类）
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)

        logger.info(f"[ArxivSpider] Total unique papers: {len(unique_articles)}")
        return unique_articles[:max_results]

    async def fetch_article(self, article_id: str) -> Optional[Article]:
        """Fetch single paper details by arXiv ID."""
        url = f"{self.base_url}?id_list={article_id}"

        try:
            response = await self._fetch_with_retry(url)
            if not response:
                return None

            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            entry = root.find("atom:entry", ns)
            if not entry:
                return None

            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            published = entry.find("atom:published", ns)
            link = entry.find("atom:id", ns)

            return Article(
                title=self._clean_text(title.text if title is not None else ""),
                content=self._clean_text(summary.text if summary is not None else ""),
                summary=self._clean_text(summary.text[:500] if summary is not None else ""),
                url=link.text if link is not None else "",
                source="arXiv",
                published_at=self.parse_datetime(published.text if published is not None else ""),
            )

        except Exception as e:
            logger.error(f"[ArxivSpider] Error fetching article {article_id}: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean text by removing extra whitespace."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


class SemanticScholarSpider(BaseSpider):
    """Semantic Scholar API Spider for earthquake research."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, config: SpiderConfig = None):
        super().__init__(config or SpiderConfig())
        import os
        self.api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

    async def _get_headers(self):
        """Get request headers."""
        headers = {
            "Accept": "application/json"
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def search(self, query: str = "") -> List[Article]:
        """Search papers from Semantic Scholar."""
        keywords = query or " ".join(self.config.keywords[:2]) if self.config.keywords else "earthquake seismology"
        fields = "title,abstract,authors,year,venue,citationCount,url,publishedDate"

        url = f"{self.BASE_URL}/paper/search?query={keywords}&limit={self.config.max_results}&fields={fields}"

        try:
            # Rate limiting: wait before request
            import asyncio
            await asyncio.sleep(2)

            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(url, headers=await self._get_headers())

            if response.status_code == 429:
                logger.warning("[SemanticScholarSpider] Rate limited (429). Consider getting an API key from https://www.semanticscholar.org/product/api")
                return []
            elif response.status_code != 200:
                logger.warning(f"[SemanticScholarSpider] HTTP {response.status_code}")
                return []

            data = response.json()
            papers = data.get("data", [])

            articles = []
            for paper in papers:
                authors = ", ".join([
                    author.get("name", "")
                    for author in paper.get("authors", [])[:5]
                ]) + ("..." if len(paper.get("authors", [])) > 5 else "")

                article = Article(
                    title=paper.get("title", "")[:500] if paper.get("title") else "",
                    summary=paper.get("abstract", "")[:500] if paper.get("abstract") else "",
                    url=paper.get("url", ""),
                    source="Semantic Scholar",
                    author=authors[:500] if authors else "",
                    published_at=self.parse_datetime(paper.get("publishedDate", "")) if paper.get("publishedDate") else None,
                    extra_info={
                        "citationCount": paper.get("citationCount", 0),
                        "venue": paper.get("venue", ""),
                        "year": paper.get("year", 0)
                    }
                )
                articles.append(article)

            logger.info(f"[SemanticScholarSpider] Fetched {len(articles)} papers")
            return articles

        except Exception as e:
            logger.error(f"[SemanticScholarSpider] Error: {e}")
            return []

    async def fetch_article(self, article_id: str) -> Optional[Article]:
        """Fetch single paper details by Semantic Scholar paper ID."""
        import asyncio
        await asyncio.sleep(2)  # Rate limiting

        fields = "title,abstract,authors,year,venue,citationCount,url,publishedDate,references,influentialCitationCount"
        url = f"{self.BASE_URL}/paper/{article_id}?fields={fields}"

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.get(url, headers=await self._get_headers())

            if response.status_code != 200:
                return None

            paper = response.json()

            authors = ", ".join([
                author.get("name", "")
                for author in paper.get("authors", [])[:5]
            ]) + ("..." if len(paper.get("authors", [])) > 5 else "")

            return Article(
                title=paper.get("title", "")[:500] if paper.get("title") else "",
                summary=paper.get("abstract", "")[:500] if paper.get("abstract") else "",
                url=paper.get("url", ""),
                source="Semantic Scholar",
                author=authors[:500] if authors else "",
                published_at=self.parse_datetime(paper.get("publishedDate", "")) if paper.get("publishedDate") else None,
                extra_info={
                    "citationCount": paper.get("citationCount", 0),
                    "influentialCitationCount": paper.get("influentialCitationCount", 0),
                    "venue": paper.get("venue", ""),
                    "year": paper.get("year", 0)
                }
            )

        except Exception as e:
            logger.error(f"[SemanticScholarSpider] Error fetching paper {article_id}: {e}")
            return None

    def parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse date string."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%Y")
            except ValueError:
                return None


class OpenAlexSpider(BaseSpider):
    """OpenAlex Academic Graph API Spider."""

    BASE_URL = "https://api.openalex.org"

    def _reconstruct_abstract(self, inverted_index: dict) -> str:
        """Reconstruct abstract text from OpenAlex inverted index."""
        if not inverted_index:
            return ""
        # Sort by position and join words
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort(key=lambda x: x[0])
        return " ".join(word for _, word in word_positions)

    async def search(self, query: str = "") -> List[Article]:
        """Search papers from OpenAlex."""
        keywords = query or " ".join(self.config.keywords[:2]) if self.config.keywords else "earthquake seismology"
        filter_str = "from_publication_date:2020-01-01,to_publication_date:2026-12-31"

        url = f"{self.BASE_URL}/works?search={keywords}&filter={filter_str}&per_page={self.config.max_results}"

        try:
            response = await self._fetch_with_retry(url)
            if not response:
                return []

            data = response.json()
            works = data.get("results", [])

            articles = []
            for work in works:
                authorships = work.get("authorships", [])
                authors = ", ".join([
                    author.get("author", {}).get("display_name", "")
                    for author in authorships[:5]
                ]) + ("..." if len(authorships) > 5 else "")

                abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))
                article = Article(
                    title=work.get("title", ""),
                    content=abstract,
                    summary=abstract[:500] if abstract else work.get("title", ""),
                    url=work.get("doi", ""),
                    source="OpenAlex",
                    author=authors,
                    published_at=self.parse_datetime(work.get("publication_date", "")) if work.get("publication_date") else None,
                    extra_info={
                        "citedByCount": work.get("cited_by_count", 0),
                        "concept": [c.get("display_name", "") for c in work.get("concepts", [])[:5]],
                        "doi": work.get("doi", "")
                    }
                )
                articles.append(article)

            logger.info(f"[OpenAlexSpider] Fetched {len(articles)} papers")
            return articles

        except Exception as e:
            logger.error(f"[OpenAlexSpider] Error: {e}")
            return []

    async def fetch_article(self, article_id: str) -> Optional[Article]:
        """Fetch single paper details."""
        url = f"{self.BASE_URL}/works/{article_id}"

        try:
            response = await self._fetch_with_retry(url)
            if not response:
                return None

            work = response.json()
            abstract = self._reconstruct_abstract(work.get("abstract_inverted_index"))

            return Article(
                title=work.get("title", ""),
                content=abstract,
                summary=abstract[:500] if abstract else work.get("title", ""),
                url=work.get("doi", ""),
                source="OpenAlex",
                published_at=self.parse_datetime(work.get("publication_date", "")) if work.get("publication_date") else None,
                extra_info={
                    "citedByCount": work.get("cited_by_count", 0),
                    "doi": work.get("doi", "")
                }
            )

        except Exception as e:
            logger.error(f"[OpenAlexSpider] Error fetching paper {article_id}: {e}")
            return None

    def parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse date string."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None
