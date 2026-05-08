"""Article API routes."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.translation import translation_service
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


class ArticleWithTranslation(BaseModel):
    """Article with bilingual translation."""
    id: int
    title: str
    title_zh: Optional[str] = None
    content: str
    content_zh: Optional[str] = None
    summary: str
    summary_zh: Optional[str] = None
    url: str
    source: str
    author: str
    published_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class TranslationRequest(BaseModel):
    text: str
    target_lang: str = "zh"  # "zh" for Chinese, "en" for English


class TranslationResponse(BaseModel):
    original: str
    translated: str
    target_lang: str


class TranslationContentResponse(BaseModel):
    """Response for on-demand translation of summary and content."""
    summary_zh: Optional[str] = None
    content_zh: Optional[str] = None


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


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Translate text to specified language."""
    if request.target_lang == "zh":
        translated = await translation_service.translate_to_chinese(request.text)
    else:
        translated = await translation_service.translate_to_english(request.text)

    if translated is None:
        raise HTTPException(status_code=500, detail="翻译服务暂时不可用")

    return TranslationResponse(
        original=request.text,
        translated=translated,
        target_lang=request.target_lang
    )


@router.get("/{article_id}/detail", response_model=ArticleWithTranslation)
async def get_article_with_translation(article_id: int, db: Session = Depends(get_db)):
    """Get article with automatic translation to Chinese."""
    service = ArticleService(db)
    article = service.get_article(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # Prepare response with original content
    response = ArticleWithTranslation(
        id=article.id,
        title=article.title,
        content=article.content or "",
        summary=article.summary or "",
        url=article.url,
        source=article.source,
        author=article.author,
        published_at=article.published_at,
        created_at=article.created_at
    )

    # Only translate title initially (summary/content translated on demand)
    title_chinese_chars = sum(1 for c in article.title if '\u4e00' <= c <= '\u9fff')
    title_needs_translation = len(article.title) > 0 and (title_chinese_chars / len(article.title)) < 0.3

    if title_needs_translation:
        title_zh = await translation_service.translate_to_chinese(article.title)
        if title_zh:
            response.title_zh = title_zh

    return response


@router.get("/{article_id}/translate", response_model=TranslationContentResponse)
async def translate_article_content(article_id: int, db: Session = Depends(get_db)):
    """Translate article summary and content on demand."""
    service = ArticleService(db)
    article = service.get_article(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    result = TranslationContentResponse()

    # Translate summary
    if article.summary:
        summary_chinese_chars = sum(1 for c in article.summary if '\u4e00' <= c <= '\u9fff')
        summary_needs_translation = (summary_chinese_chars / len(article.summary)) < 0.3

        if summary_needs_translation:
            summary_zh = await translation_service.translate_to_chinese(article.summary)
            if summary_zh:
                result.summary_zh = summary_zh

    # Translate content if different from summary
    if article.content and article.content != article.summary:
        content_chinese_chars = sum(1 for c in article.content if '\u4e00' <= c <= '\u9fff')
        content_needs_translation = (content_chinese_chars / len(article.content)) < 0.3

        if content_needs_translation:
            content_zh = await translation_service.translate_to_chinese(article.content)
            if content_zh:
                result.content_zh = content_zh

    return result
