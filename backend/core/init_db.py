"""Database initialization script."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import engine, Base
from core.models import (
    Industry, DataSource, CrawlLog, Article,
    ContentFingerprint, EarthquakeEvent, Statistics, PluginConfig
)


def init_db():
    """Initialize database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


def create_default_industry(db):
    """Create default earthquake industry."""
    from sqlalchemy.orm import Session
    from core.database import SessionLocal

    db = SessionLocal()
    try:
        existing = db.query(Industry).filter(Industry.name == "地震行业").first()
        if not existing:
            industry = Industry(
                name="地震行业",
                keywords=["earthquake", "seismology", "seismic", "地震", "震源", "抗震", "地震预警"],
                enabled=True
            )
            db.add(industry)
            db.commit()
            print("Default earthquake industry created!")

            # Create default data sources
            create_default_data_sources(db, industry.id)
        else:
            print("Earthquake industry already exists.")
    finally:
        db.close()


def create_default_data_sources(db, industry_id):
    """Create default earthquake data sources.

    Data source categories:
    - Monitoring: Earthquake monitoring networks (USGS, China, EMSC, etc.)
    - Academic: Scholarly articles and preprints (arXiv, Semantic Scholar, OpenAlex, etc.)
    - Patent: Patent databases (USPTO, EPO, WIPO)
    - News: News sources and RSS feeds
    - Government: Government statistical data (World Bank, OECD, etc.)
    - Financial: Economic indicators (FRED, etc.)
    - Weather: Weather and climate data (OpenWeatherMap, NASA, etc.)
    - Social: Social media data (Reddit, etc.)
    """
    data_sources = [
        # ============ 地震监测 (Earthquake Monitoring) ============
        {
            "name": "USGS全球地震目录",
            "source_type": "monitoring",
            "base_url": "https://earthquake.usgs.gov/fdsnws/event/1/query",
            "spider_class": "USGSSpider",
            "enabled": True,
            "keywords": ["earthquake", "seismic"],
            "update_interval": 300
        },
        {
            "name": "中国地震台网",
            "source_type": "monitoring",
            "base_url": "https://data.earthquake.cn/datashare/globeEarthquake_csn",
            "spider_class": "ChinaEarthquakeSpider",
            "enabled": True,
            "keywords": ["地震", "震级", "震源"],
            "update_interval": 600
        },
        {
            "name": "EMSC欧洲地中海地震中心",
            "source_type": "monitoring",
            "base_url": "https://www.seismicportal.eu/fdsnws/event/1/query",
            "spider_class": "EMSCSpider",
            "enabled": True,
            "keywords": ["earthquake", "mediterranean"],
            "update_interval": 600
        },
        {
            "name": "ISC国际地震中心",
            "source_type": "monitoring",
            "base_url": "https://www.isc.ac.uk/fdsnws/event/1/query",
            "spider_class": "ISCSpider",
            "enabled": True,
            "keywords": ["earthquake", "seismic", "bulletin"],
            "update_interval": 3600
        },
        {
            "name": "GCMT全球矩心矩张量",
            "source_type": "monitoring",
            "base_url": "https://www.globalcmt.org/cgi/globalcmt-cgi-bin/CMT5/form",
            "spider_class": "GCMTSpider",
            "enabled": True,
            "keywords": ["moment tensor", "CMT", "focal mechanism"],
            "update_interval": 86400
        },
        {
            "name": "FNET日本地震海啸监测",
            "source_type": "monitoring",
            "base_url": "https://www.fnet.bosai.go.jp/auth/jsta/catalog_fnet-eng.php",
            "spider_class": "FNETSpider",
            "enabled": False,
            "keywords": ["earthquake", "Japan", "tsunami"],
            "update_interval": 600
        },

        # ============ 学术文献 (Academic) ============
        {
            "name": "arXiv地震学预印本",
            "source_type": "academic",
            "base_url": "http://export.arxiv.org/api/query",
            "spider_class": "ArxivSeismologySpider",
            "enabled": True,
            "keywords": ["earthquake", "seismology", "seismic wave", "ground motion"],
            "update_interval": 7200
        },
        {
            "name": "Semantic Scholar地震研究",
            "source_type": "academic",
            "base_url": "https://api.semanticscholar.org/graph/v1/paper/search",
            "spider_class": "SemanticScholarSpider",
            "enabled": True,
            "keywords": ["earthquake engineering", "seismic design", "seismology"],
            "update_interval": 3600
        },
        {
            "name": "OpenAlex学术知识库",
            "source_type": "academic",
            "base_url": "https://api.openalex.org/works",
            "spider_class": "OpenAlexSpider",
            "enabled": True,
            "keywords": ["earthquake", "seismology", "seismic hazard"],
            "update_interval": 7200
        },
        {
            "name": "CrossRef元数据",
            "source_type": "academic",
            "base_url": "https://api.crossref.org/works",
            "spider_class": "CrossRefSpider",
            "enabled": True,
            "keywords": ["earthquake", "seismic", "geophysics"],
            "update_interval": 7200
        },
        {
            "name": "PubMed医学文献",
            "source_type": "academic",
            "base_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            "spider_class": "PubMedSpider",
            "enabled": False,
            "keywords": ["earthquake", "trauma", "disaster medicine"],
            "update_interval": 14400
        },
        {
            "name": "CORE开放获取论文",
            "source_type": "academic",
            "base_url": "https://api.core.ac.uk/v3/search/works",
            "spider_class": "CORESpider",
            "enabled": True,
            "keywords": ["earthquake", "seismic engineering"],
            "update_interval": 7200
        },

        # ============ 专利 (Patent) ============
        {
            "name": "USPTO美国专利局",
            "source_type": "patent",
            "base_url": "https://developer.uspto.gov/api/v1/patents",
            "spider_class": "USPTOPatentSpider",
            "enabled": True,
            "keywords": ["seismic", "earthquake resistant", "vibration damping"],
            "update_interval": 86400
        },
        {
            "name": "EPO欧洲专利局",
            "source_type": "patent",
            "base_url": "https://ops.epo.org/3.2/rest-services/register/publication/EP",
            "spider_class": "EPOSpider",
            "enabled": True,
            "keywords": ["seismic", "earthquake protection"],
            "update_interval": 86400
        },
        {
            "name": "Google Patents",
            "source_type": "patent",
            "base_url": "https://patents.google.com/xhr/query",
            "spider_class": "GooglePatentsSpider",
            "enabled": True,
            "keywords": ["earthquake engineering", "seismic design"],
            "update_interval": 86400
        },
        {
            "name": "WIPO国际知识产权组织",
            "source_type": "patent",
            "base_url": "https://patentscope.wipo.int/search/en/search.jsf",
            "spider_class": "WIPOSpider",
            "enabled": False,
            "keywords": ["earthquake", "seismic isolation"],
            "update_interval": 86400
        },
        {
            "name": "CNIPA中国国家知识产权局",
            "source_type": "patent",
            "base_url": "https://pss-system.cponline.cnipa.gov.cn",
            "spider_class": "CNIPASpider",
            "enabled": True,
            "keywords": ["抗震", "地震", "减震", "隔震"],
            "update_interval": 86400
        },

        # ============ 新闻 (News) ============
        {
            "name": "应急管理部新闻",
            "source_type": "news",
            "base_url": "https://www.mem.gov.cn/xw/zhsgxx",
            "spider_class": "EmergencyNewsSpider",
            "enabled": True,
            "keywords": ["地震", "应急", "灾害", "抗震"],
            "update_interval": 1800
        },
        {
            "name": "中国地震局新闻",
            "source_type": "news",
            "base_url": "http://www.cea.gov.cn/cea/xwzx/zyzt/index.html",
            "spider_class": "ChinaEarthquakeBureauSpider",
            "enabled": True,
            "keywords": ["地震", "震情", "地震预报"],
            "update_interval": 1800
        },
        {
            "name": "NewsAPI全球新闻",
            "source_type": "news",
            "base_url": "https://newsapi.org/v2/everything",
            "spider_class": "NewsAPISpider",
            "enabled": True,
            "keywords": ["earthquake", "seismic", "tsunami"],
            "update_interval": 3600
        },
        {
            "name": "中国地震台网速报",
            "source_type": "news",
            "base_url": "https://news.ceic.ac.cn/",
            "spider_class": "CEICNewsSpider",
            "enabled": True,
            "keywords": ["地震", "速报", "震情"],
            "update_interval": 300
        },
        {
            "name": "RSS新华网",
            "source_type": "news",
            "base_url": "http://www.news.cn/rss/tech.xml",
            "spider_class": "RSSSpider",
            "enabled": True,
            "keywords": ["地震", "灾害", "应急"],
            "update_interval": 1800
        },
        {
            "name": "RSS人民网",
            "source_type": "news",
            "base_url": "http://paper.people.com.cn/rss/technology.xml",
            "spider_class": "RSSSpider",
            "enabled": True,
            "keywords": ["地震", "科技"],
            "update_interval": 1800
        },

        # ============ 政府数据 (Government) ============
        {
            "name": "World Bank世界银行数据",
            "source_type": "government",
            "base_url": "https://api.worldbank.org/v2",
            "spider_class": "WorldBankSpider",
            "enabled": True,
            "keywords": ["disaster", "risk", "climate"],
            "update_interval": 86400
        },
        {
            "name": "OECD经济合作与发展组织",
            "source_type": "government",
            "base_url": "https://stats.oecd.org/SDMX-JSON/data",
            "spider_class": "OECDSpider",
            "enabled": False,
            "keywords": ["economic", "disaster risk"],
            "update_interval": 86400
        },
        {
            "name": "中国国家统计局",
            "source_type": "government",
            "base_url": "https://data.stats.gov.cn/easyquery.htm",
            "spider_class": "ChinaStatsSpider",
            "enabled": False,
            "keywords": ["GDP", "population", "economic"],
            "update_interval": 86400
        },

        # ============ 金融经济 (Financial) ============
        {
            "name": "FRED美联储经济数据",
            "source_type": "government",
            "base_url": "https://api.stlouisfed.org/fred/series/observations",
            "spider_class": "FREDSpider",
            "enabled": True,
            "keywords": ["GDP", "inflation", "economic indicators"],
            "update_interval": 86400
        },
        {
            "name": "Alpha Vantage金融数据",
            "source_type": "government",
            "base_url": "https://www.alphavantage.co/query",
            "spider_class": "AlphaVantageSpider",
            "enabled": False,
            "keywords": ["stock", "commodity", "economic"],
            "update_interval": 3600
        },

        # ============ 气象环境 (Weather/Environment) ============
        {
            "name": "OpenWeatherMap天气API",
            "source_type": "monitoring",
            "base_url": "https://api.openweathermap.org/data/2.5/weather",
            "spider_class": "OpenWeatherSpider",
            "enabled": True,
            "keywords": ["weather", "climate", "temperature"],
            "update_interval": 3600
        },
        {
            "name": "Open-Meteo开源天气",
            "source_type": "monitoring",
            "base_url": "https://api.open-meteo.com/v1/forecast",
            "spider_class": "OpenMeteoSpider",
            "enabled": True,
            "keywords": ["weather", "forecast", "climate"],
            "update_interval": 3600
        },
        {
            "name": "NASA POWER气象数据",
            "source_type": "monitoring",
            "base_url": "https://power.larc.nasa.gov/api/temporal/daily/point",
            "spider_class": "NASAPOWERSpider",
            "enabled": False,
            "keywords": ["solar", "meteorological", "climate"],
            "update_interval": 86400
        },
        {
            "name": "中国空气质量数据",
            "source_type": "monitoring",
            "base_url": "https://aqicn.org/data-platform/register/",
            "spider_class": "AQICNSpider",
            "enabled": False,
            "keywords": ["AQI", "PM2.5", "air quality"],
            "update_interval": 3600
        },

        # ============ 地理编码 (Geocoding) ============
        {
            "name": "Nominatim地理编码",
            "source_type": "monitoring",
            "base_url": "https://nominatim.openstreetmap.org/search",
            "spider_class": "NominatimSpider",
            "enabled": True,
            "keywords": ["geocoding", "location", "coordinates"],
            "update_interval": 604800
        },
        {
            "name": "Open-Meteo地理编码",
            "source_type": "monitoring",
            "base_url": "https://geocoding-api.open-meteo.com/v1/search",
            "spider_class": "OpenMeteoGeocodingSpider",
            "enabled": True,
            "keywords": ["city", "location", "search"],
            "update_interval": 604800
        },

        # ============ 社交媒体 (Social) ============
        {
            "name": "Reddit科技讨论",
            "source_type": "social",
            "base_url": "https://www.reddit.com/r/technology",
            "spider_class": "RedditSpider",
            "enabled": False,
            "keywords": ["earthquake", "disaster", "seismic"],
            "update_interval": 1800
        },
        {
            "name": "Reddit科学讨论",
            "source_type": "social",
            "base_url": "https://www.reddit.com/r/science",
            "spider_class": "RedditScienceSpider",
            "enabled": False,
            "keywords": ["earthquake", "geology", "seismology"],
            "update_interval": 1800
        },
    ]

    for ds_data in data_sources:
        existing = db.query(DataSource).filter(DataSource.name == ds_data["name"]).first()
        if not existing:
            ds = DataSource(industry_id=industry_id, **ds_data)
            db.add(ds)

    db.commit()
    print(f"Created {len(data_sources)} default data sources!")


if __name__ == "__main__":
    init_db()
    create_default_industry(None)
