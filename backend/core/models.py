"""Database models for IntelliKnow."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    Enum as SQLEnum, JSON, ForeignKey, BigInteger, UniqueConstraint
)
from sqlalchemy.orm import relationship
from core.database import Base
import enum


class SourceType(str, enum.Enum):
    """Data source types."""
    ACADEMIC = "academic"
    NEWS = "news"
    PATENT = "patent"
    GOVERNMENT = "government"
    MONITORING = "monitoring"
    SOCIAL = "social"


class CrawlStatus(str, enum.Enum):
    """Crawl status."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class Industry(Base):
    """Industry configuration table."""
    __tablename__ = "industry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="行业名称")
    keywords = Column(JSON, comment="关键词列表")
    enabled = Column(Boolean, default=True, comment="启用状态")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    articles = relationship("Article", back_populates="industry")
    data_sources = relationship("DataSource", back_populates="industry")


class DataSource(Base):
    """Data source configuration table."""
    __tablename__ = "data_source"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="数据源名称")
    source_type = Column(SQLEnum(SourceType), nullable=False, comment="数据源类型")
    base_url = Column(String(500), nullable=False, comment="API基础地址")
    spider_class = Column(String(200), comment="对应爬虫类名")
    enabled = Column(Boolean, default=True)
    config_json = Column(JSON, comment="扩展配置")
    rate_limit = Column(Integer, default=10, comment="请求频率限制(秒)")
    keywords = Column(JSON, comment="搜索关键词列表")
    update_interval = Column(Integer, default=3600, comment="更新间隔(秒)")
    last_crawl_at = Column(DateTime, comment="最后爬取时间")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    industry_id = Column(Integer, ForeignKey("industry.id"), nullable=True)
    industry = relationship("Industry", back_populates="data_sources")
    crawl_logs = relationship("CrawlLog", back_populates="data_source")


class CrawlLog(Base):
    """Crawl log table."""
    __tablename__ = "crawl_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("data_source.id"), nullable=False)
    articles_count = Column(Integer, default=0, comment="爬取文章数")
    status = Column(SQLEnum(CrawlStatus), default=CrawlStatus.SUCCESS)
    error_message = Column(Text)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)

    data_source = relationship("DataSource", back_populates="crawl_logs")


class Article(Base):
    """Article table."""
    __tablename__ = "article"
    __table_args__ = (
        UniqueConstraint('title', 'source', name='uq_article_title_source'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    industry_id = Column(Integer, ForeignKey("industry.id"), nullable=True)
    title = Column(String(500), nullable=False, comment="标题")
    content = Column(Text, comment="内容")
    summary = Column(Text, comment="摘要")
    url = Column(String(1000), comment="来源URL")
    source = Column(String(100), comment="来源")
    author = Column(String(500), comment="作者")
    published_at = Column(DateTime, comment="发布时间")
    created_at = Column(DateTime, default=datetime.now)
    content_hash = Column(String(64), comment="内容指纹", index=True)
    extra_info = Column(JSON, comment="扩展信息")
    summary_zh = Column(Text, comment="中文摘要")
    content_zh = Column(Text, comment="中文内容")

    industry = relationship("Industry", back_populates="articles")
    fingerprints = relationship("ContentFingerprint", back_populates="article")


class ContentFingerprint(Base):
    """Content fingerprint table for deduplication."""
    __tablename__ = "content_fingerprint"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    article_id = Column(BigInteger, ForeignKey("article.id"), nullable=False)
    fingerprint = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)

    article = relationship("Article", back_populates="fingerprints")


class EarthquakeEvent(Base):
    """Earthquake event table for seismology industry."""
    __tablename__ = "earthquake_event"
    __table_args__ = (
        UniqueConstraint('event_id', 'source', name='uq_earthquake_event_id_source'),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(String(100), comment="外部事件ID")
    magnitude = Column(Float, comment="震级")
    latitude = Column(Float, comment="纬度")
    longitude = Column(Float, comment="经度")
    depth = Column(Float, comment="深度(km)")
    location = Column(String(500), comment="位置名称")
    region = Column(String(200), comment="区域/国家")
    time = Column(DateTime, comment="发震时刻")
    source = Column(String(100), comment="数据来源")
    created_at = Column(DateTime, default=datetime.now)


class Statistics(Base):
    """Statistics table for analysis."""
    __tablename__ = "statistics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stat_type = Column(String(50), nullable=False, comment="统计类型")
    period = Column(String(20), comment="统计周期")
    region = Column(String(200), comment="区域")
    value = Column(Float, comment="数值")
    unit = Column(String(50), comment="单位")
    extra_data = Column(JSON, comment="附加数据")
    created_at = Column(DateTime, default=datetime.now)


class PluginConfig(Base):
    """Plugin configuration table."""
    __tablename__ = "plugin_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plugin_type = Column(String(50), nullable=False, comment="插件类型")
    config_json = Column(JSON, comment="配置JSON")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
