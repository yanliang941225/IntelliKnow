"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from apps.industries.api import router as industries_router
from apps.articles.api import router as articles_router
from apps.crawlers.api import router as crawlers_router
from apps.crawlers.earthquake_api import router as earthquake_router
from apps.statistics.api import router as statistics_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting IntelliKnow application...")

    from apps.crawlers.scheduler import crawler_scheduler
    # Start scheduler directly - BackgroundScheduler doesn't need an event loop
    crawler_scheduler.start()

    yield

    # Stop scheduler
    crawler_scheduler.stop()
    logger.info("IntelliKnow application stopped")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="全球行业研究知识爬取系统 - 地震行业专用版",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(industries_router, prefix=settings.API_PREFIX)
app.include_router(articles_router, prefix=settings.API_PREFIX)
app.include_router(crawlers_router, prefix=settings.API_PREFIX)
app.include_router(earthquake_router, prefix=settings.API_PREFIX)
app.include_router(statistics_router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
