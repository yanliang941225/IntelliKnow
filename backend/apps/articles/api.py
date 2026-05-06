"""Article API routes."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from apps.articles.service import ArticleService

router = APIRouter(prefix="/articles", tags=["文章管理"])


class ArticleCreate(BaseModel):
    title: str
    content: str = ""
    summary: str = ""
    url: str = ""
    source: str = ""
    author: str = ""
    published_at: Optional[datetime] = None
    industry_id: Optional[int] = None


class ArticleResponse(BaseModel):
    id: int
    title: str
    content: str
    summary: str
    url: str
    source: str
    author: str
    published_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    items: List[ArticleResponse]
    total: int
    page: int
    page_size: int


@router.post("/", response_model=ArticleResponse)
def create_article(
    article: ArticleCreate,
    db: Session = Depends(get_db)
):
    """Create a new article."""
    service = ArticleService(db)
    result = service.create_article(
        title=article.title,
        content=article.content,
        summary=article.summary,
        url=article.url,
        source=article.source,
        author=article.author,
        published_at=article.published_at,
        industry_id=article.industry_id
    )

    if not result:
        raise HTTPException(status_code=400, detail="文章已存在或创建失败")

    return result


@router.get("/", response_model=ArticleListResponse)
def get_articles(
    industry_id: Optional[int] = None,
    source: Optional[str] = None,
    keyword: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get articles with filters."""
    service = ArticleService(db)

    items = service.get_articles(
        industry_id=industry_id,
        source=source,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size
    )

    total = service.count_articles(
        industry_id=industry_id,
        source=source,
        keyword=keyword
    )

    return ArticleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    """Get article by ID."""
    service = ArticleService(db)
    article = service.get_article(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    return article


@router.get("/search/", response_model=ArticleListResponse)
def search_articles(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search articles by keyword."""
    service = ArticleService(db)

    items = service.search_articles(q, page, page_size)
    total = service.count_articles(keyword=q)

    return ArticleListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


@router.delete("/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db)):
    """Delete article."""
    service = ArticleService(db)
    success = service.delete_article(article_id)

    if not success:
        raise HTTPException(status_code=404, detail="文章不存在")

    return {"message": "删除成功"}


@router.get("/sources/list")
def get_sources(db: Session = Depends(get_db)):
    """Get all unique sources."""
    service = ArticleService(db)
    return {"sources": service.get_sources()}
