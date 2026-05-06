"""Article management module."""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from core.models import Article, ContentFingerprint, Industry, DataSource
from apps.utils.similarity import deduplicator, ContentDeduplicator


class ArticleService:
    """Article management service."""

    def __init__(self, db: Session):
        self.db = db
        self.deduplicator = ContentDeduplicator(threshold=0.85)

    def create_article(
        self,
        title: str,
        content: str = "",
        summary: str = "",
        url: str = "",
        source: str = "",
        author: str = "",
        published_at: datetime = None,
        industry_id: int = None,
        keywords: List[str] = None
    ) -> Optional[Article]:
        """Create a new article with deduplication check."""
        if not title:
            return None

        # Fast check: exact match on title + source
        existing = self.db.query(Article).filter(
            Article.title == title,
            Article.source == source
        ).first()
        if existing:
            return None

        full_content = f"{title} {content}"
        content_hash = self.deduplicator.generate_fingerprint(full_content)

        # Check content hash
        existing_by_hash = self.db.query(Article).filter(
            Article.content_hash == content_hash
        ).first()
        if existing_by_hash:
            return None

        article = Article(
            title=title,
            content=content,
            summary=summary or content[:500] if content else "",
            url=url,
            source=source,
            author=author,
            published_at=published_at,
            industry_id=industry_id,
            content_hash=content_hash
        )

        self.db.add(article)
        self.db.flush()

        fingerprint = ContentFingerprint(
            article_id=article.id,
            fingerprint=content_hash
        )
        self.db.add(fingerprint)
        self.db.commit()
        self.db.refresh(article)

        return article

    def get_article(self, article_id: int) -> Optional[Article]:
        """Get article by ID."""
        return self.db.query(Article).filter(Article.id == article_id).first()

    def get_articles(
        self,
        industry_id: int = None,
        source: str = None,
        keyword: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Article]:
        """Get articles with filters."""
        query = self.db.query(Article)

        if industry_id:
            query = query.filter(Article.industry_id == industry_id)
        if source:
            query = query.filter(Article.source == source)
        if keyword:
            query = query.filter(
                or_(
                    Article.title.like(f"%{keyword}%"),
                    Article.content.like(f"%{keyword}%")
                )
            )
        if start_date:
            query = query.filter(Article.published_at >= start_date)
        if end_date:
            query = query.filter(Article.published_at <= end_date)

        query = query.order_by(desc(Article.published_at))

        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size).all()

    def count_articles(
        self,
        industry_id: int = None,
        source: str = None,
        keyword: str = None
    ) -> int:
        """Count articles with filters."""
        query = self.db.query(Article)

        if industry_id:
            query = query.filter(Article.industry_id == industry_id)
        if source:
            query = query.filter(Article.source == source)
        if keyword:
            query = query.filter(
                or_(
                    Article.title.like(f"%{keyword}%"),
                    Article.content.like(f"%{keyword}%")
                )
            )

        return query.count()

    def search_articles(
        self,
        query_text: str,
        page: int = 1,
        page_size: int = 20
    ) -> List[Article]:
        """Full-text search articles."""
        query = self.db.query(Article).filter(
            or_(
                Article.title.like(f"%{query_text}%"),
                Article.content.like(f"%{query_text}%"),
                Article.summary.like(f"%{query_text}%")
            )
        ).order_by(desc(Article.published_at))

        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size).all()

    def update_article(
        self,
        article_id: int,
        title: str = None,
        content: str = None,
        summary: str = None
    ) -> Optional[Article]:
        """Update article."""
        article = self.get_article(article_id)
        if not article:
            return None

        if title is not None:
            article.title = title
        if content is not None:
            article.content = content
        if summary is not None:
            article.summary = summary

        self.db.commit()
        self.db.refresh(article)
        return article

    def delete_article(self, article_id: int) -> bool:
        """Delete article."""
        article = self.get_article(article_id)
        if not article:
            return False

        self.db.query(ContentFingerprint).filter(
            ContentFingerprint.article_id == article_id
        ).delete()

        self.db.delete(article)
        self.db.commit()
        return True

    def get_sources(self) -> List[str]:
        """Get all unique sources."""
        results = self.db.query(Article.source).distinct().all()
        return [r[0] for r in results if r[0]]
