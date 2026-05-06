"""Data source API routes."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import DataSource, SourceType
from apps.crawlers.scheduler import crawler_scheduler

router = APIRouter(prefix="/datasources", tags=["数据源管理"])


class DataSourceCreate(BaseModel):
    name: str
    source_type: str
    base_url: str
    spider_class: str
    enabled: bool = True
    config_json: dict = None
    rate_limit: int = 10
    keywords: List[str] = []
    update_interval: int = 3600
    industry_id: Optional[int] = None


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    base_url: Optional[str] = None
    spider_class: Optional[str] = None
    enabled: Optional[bool] = None
    config_json: Optional[dict] = None
    rate_limit: Optional[int] = None
    keywords: Optional[List[str]] = None
    update_interval: Optional[int] = None


class DataSourceResponse(BaseModel):
    id: int
    name: str
    source_type: str
    base_url: str
    spider_class: str
    enabled: bool
    rate_limit: int
    update_interval: int
    last_crawl_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[DataSourceResponse])
def get_datasources(
    enabled: Optional[bool] = None,
    source_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all data sources."""
    query = db.query(DataSource)

    if enabled is not None:
        query = query.filter(DataSource.enabled == enabled)
    if source_type:
        query = query.filter(DataSource.source_type == source_type)

    return query.order_by(DataSource.created_at.desc()).all()


@router.post("/", response_model=DataSourceResponse)
def create_datasource(
    datasource: DataSourceCreate,
    db: Session = Depends(get_db)
):
    """Create a new data source."""
    try:
        source_type = SourceType(datasource.source_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid source_type: {datasource.source_type}")

    ds = DataSource(
        name=datasource.name,
        source_type=source_type,
        base_url=datasource.base_url,
        spider_class=datasource.spider_class,
        enabled=datasource.enabled,
        config_json=datasource.config_json,
        rate_limit=datasource.rate_limit,
        keywords=datasource.keywords,
        update_interval=datasource.update_interval,
        industry_id=datasource.industry_id
    )

    db.add(ds)
    db.commit()
    db.refresh(ds)

    if ds.enabled:
        crawler_scheduler.add_source(ds.id)

    return ds


@router.get("/{source_id}", response_model=DataSourceResponse)
def get_datasource(source_id: int, db: Session = Depends(get_db)):
    """Get data source by ID."""
    ds = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return ds


@router.put("/{source_id}", response_model=DataSourceResponse)
def update_datasource(
    source_id: int,
    datasource: DataSourceUpdate,
    db: Session = Depends(get_db)
):
    """Update data source."""
    ds = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    update_data = datasource.model_dump(exclude_unset=True)

    if "source_type" in update_data:
        try:
            update_data["source_type"] = SourceType(update_data["source_type"])
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid source_type")

    for key, value in update_data.items():
        setattr(ds, key, value)

    db.commit()
    db.refresh(ds)

    if "enabled" in update_data:
        if ds.enabled:
            crawler_scheduler.add_source(ds.id)
        else:
            crawler_scheduler.remove_source(ds.id)
    elif ds.enabled:
        crawler_scheduler.add_source(ds.id)

    return ds


@router.delete("/{source_id}")
def delete_datasource(source_id: int, db: Session = Depends(get_db)):
    """Delete data source."""
    ds = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    crawler_scheduler.remove_source(source_id)

    db.delete(ds)
    db.commit()

    return {"message": "删除成功"}


@router.post("/{source_id}/crawl")
def trigger_crawl(source_id: int, db: Session = Depends(get_db)):
    """Trigger immediate crawl for a data source."""
    ds = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    crawler_scheduler.crawl_now(source_id)

    return {"message": "爬取任务已触发", "source_id": source_id}


@router.post("/{source_id}/toggle")
def toggle_datasource(source_id: int, db: Session = Depends(get_db)):
    """Toggle data source enabled status."""
    ds = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="数据源不存在")

    ds.enabled = not ds.enabled
    db.commit()
    db.refresh(ds)

    if ds.enabled:
        crawler_scheduler.add_source(ds.id)
    else:
        crawler_scheduler.remove_source(ds.id)

    return {"enabled": ds.enabled, "message": f"已{'启用' if ds.enabled else '禁用'}"}
