-- IntelliKnow Database Schema
-- SQLite initialization script

-- Industry table
CREATE TABLE IF NOT EXISTS industry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    keywords JSON,
    enabled BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Data source configuration table
CREATE TABLE IF NOT EXISTS data_source (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    spider_class VARCHAR(200),
    enabled BOOLEAN DEFAULT 1,
    config_json JSON,
    rate_limit INTEGER DEFAULT 10,
    keywords JSON,
    update_interval INTEGER DEFAULT 3600,
    last_crawl_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    industry_id INTEGER,
    FOREIGN KEY (industry_id) REFERENCES industry(id)
);

-- Crawl log table
CREATE TABLE IF NOT EXISTS crawl_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    articles_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT,
    started_at DATETIME NOT NULL,
    completed_at DATETIME,
    FOREIGN KEY (source_id) REFERENCES data_source(id)
);

-- Article table
CREATE TABLE IF NOT EXISTS article (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry_id INTEGER,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    summary TEXT,
    url VARCHAR(1000),
    source VARCHAR(100),
    author VARCHAR(500),
    published_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    content_hash VARCHAR(64),
    extra_info JSON,
    FOREIGN KEY (industry_id) REFERENCES industry(id),
    UNIQUE(title, source)
);

CREATE INDEX IF NOT EXISTS idx_article_content_hash ON article(content_hash);

-- Content fingerprint table
CREATE TABLE IF NOT EXISTS content_fingerprint (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    fingerprint VARCHAR(64) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES article(id)
);

CREATE INDEX IF NOT EXISTS idx_fingerprint ON content_fingerprint(fingerprint);

-- Earthquake event table
CREATE TABLE IF NOT EXISTS earthquake_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id VARCHAR(100),
    magnitude REAL,
    latitude REAL,
    longitude REAL,
    depth REAL,
    location VARCHAR(500),
    region VARCHAR(200),
    time DATETIME,
    source VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, source)
);

-- Statistics table
CREATE TABLE IF NOT EXISTS statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_type VARCHAR(50) NOT NULL,
    period VARCHAR(20),
    region VARCHAR(200),
    value REAL,
    unit VARCHAR(50),
    extra_data JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Plugin configuration table
CREATE TABLE IF NOT EXISTS plugin_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plugin_type VARCHAR(50) NOT NULL,
    config_json JSON,
    enabled BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert default earthquake industry
INSERT OR IGNORE INTO industry (id, name, keywords, enabled)
VALUES (1, '地震行业', '["earthquake", "seismology", "seismic", "地震", "震源", "抗震", "地震预警"]', 1);

-- Insert default data sources
INSERT OR IGNORE INTO data_source (id, name, source_type, base_url, spider_class, enabled, keywords, update_interval, industry_id) VALUES
(1, 'USGS全球地震目录', 'monitoring', 'https://earthquake.usgs.gov/fdsnws/event/1/query', 'USGSSpider', 1, '["earthquake", "seismic"]', 300, 1),
(2, '中国地震台网', 'monitoring', 'https://data.earthquake.cn/datashare/globeEarthquake_csn', 'ChinaEarthquakeSpider', 1, '["地震", "震级", "震源"]', 600, 1),
(3, 'EMSC欧洲地中海地震中心', 'monitoring', 'https://www.seismicportal.eu/fdsnws/event/1/query', 'EMSCSpider', 1, '["earthquake", "mediterranean"]', 600, 1),
(4, 'ISC国际地震中心', 'monitoring', 'https://www.isc.ac.uk/fdsnws/event/1/query', 'ISCSpider', 1, '["earthquake", "seismic", "bulletin"]', 3600, 1),
(5, 'GCMT全球矩心矩张量', 'monitoring', 'https://www.globalcmt.org/cgi/globalcmt-cgi-bin/CMT5/form', 'GCMTSpider', 1, '["moment tensor", "CMT", "focal mechanism"]', 86400, 1),
(6, 'FNET日本地震海啸监测', 'monitoring', 'https://www.fnet.bosai.go.jp/auth/jsta/catalog_fnet-eng.php', 'FNETSpider', 0, '["earthquake", "Japan", "tsunami"]', 600, 1),
(7, 'arXiv地震学预印本', 'academic', 'http://export.arxiv.org/api/query', 'ArxivSeismologySpider', 1, '["earthquake", "seismology", "seismic wave", "ground motion"]', 7200, 1),
(8, 'Semantic Scholar地震研究', 'academic', 'https://api.semanticscholar.org/graph/v1/paper/search', 'SemanticScholarSpider', 1, '["earthquake engineering", "seismic design", "seismology"]', 3600, 1),
(9, 'OpenAlex学术知识库', 'academic', 'https://api.openalex.org/works', 'OpenAlexSpider', 1, '["earthquake", "seismology", "seismic hazard"]', 7200, 1),
(10, 'CrossRef元数据', 'academic', 'https://api.crossref.org/works', 'CrossRefSpider', 1, '["earthquake", "seismic", "geophysics"]', 7200, 1),
(11, 'PubMed医学文献', 'academic', 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi', 'PubMedSpider', 0, '["earthquake", "trauma", "disaster medicine"]', 14400, 1),
(12, 'CORE开放获取论文', 'academic', 'https://api.core.ac.uk/v3/search/works', 'CORESpider', 1, '["earthquake", "seismic engineering"]', 7200, 1),
(13, 'USPTO美国专利局', 'patent', 'https://developer.uspto.gov/api/v1/patents', 'USPTOPatentSpider', 1, '["seismic", "earthquake resistant", "vibration damping"]', 86400, 1),
(14, 'EPO欧洲专利局', 'patent', 'https://ops.epo.org/3.2/rest-services/register/publication/EP', 'EPOSpider', 1, '["seismic", "earthquake protection"]', 86400, 1),
(15, 'Google Patents', 'patent', 'https://patents.google.com/xhr/query', 'GooglePatentsSpider', 1, '["earthquake engineering", "seismic design"]', 86400, 1),
(16, 'WIPO国际知识产权组织', 'patent', 'https://patentscope.wipo.int/search/en/search.jsf', 'WIPOSpider', 0, '["earthquake", "seismic isolation"]', 86400, 1),
(17, 'CNIPA中国国家知识产权局', 'patent', 'https://pss-system.cponline.cnipa.gov.cn', 'CNIPASpider', 1, '["抗震", "地震", "减震", "隔震"]', 86400, 1),
(18, '应急管理部新闻', 'news', 'https://www.mem.gov.cn/xw/zhsgxx', 'EmergencyNewsSpider', 1, '["地震", "应急", "灾害", "抗震"]', 1800, 1),
(19, '中国地震局新闻', 'news', 'http://www.cea.gov.cn/cea/xwzx/zyzt/index.html', 'ChinaEarthquakeBureauSpider', 1, '["地震", "震情", "地震预报"]', 1800, 1),
(20, 'NewsAPI全球新闻', 'news', 'https://newsapi.org/v2/everything', 'NewsAPISpider', 1, '["earthquake", "seismic", "tsunami"]', 3600, 1),
(21, '中国地震台网速报', 'news', 'https://news.ceic.ac.cn/', 'CEICNewsSpider', 1, '["地震", "速报", "震情"]', 300, 1),
(22, 'RSS新华网', 'news', 'http://www.news.cn/rss/tech.xml', 'RSSSpider', 1, '["地震", "灾害", "应急"]', 1800, 1),
(23, 'RSS人民网', 'news', 'http://paper.people.com.cn/rss/technology.xml', 'RSSSpider', 1, '["地震", "科技"]', 1800, 1),
(24, 'World Bank世界银行数据', 'government', 'https://api.worldbank.org/v2', 'WorldBankSpider', 1, '["disaster", "risk", "climate"]', 86400, 1),
(25, 'OECD经济合作与发展组织', 'government', 'https://stats.oecd.org/SDMX-JSON/data', 'OECDSpider', 0, '["economic", "disaster risk"]', 86400, 1),
(26, '中国国家统计局', 'government', 'https://data.stats.gov.cn/easyquery.htm', 'ChinaStatsSpider', 0, '["GDP", "population", "economic"]', 86400, 1),
(27, 'FRED美联储经济数据', 'government', 'https://api.stlouisfed.org/fred/series/observations', 'FREDSpider', 1, '["GDP", "inflation", "economic indicators"]', 86400, 1),
(28, 'Alpha Vantage金融数据', 'government', 'https://www.alphavantage.co/query', 'AlphaVantageSpider', 0, '["stock", "commodity", "economic"]', 3600, 1),
(29, 'OpenWeatherMap天气API', 'monitoring', 'https://api.openweathermap.org/data/2.5/weather', 'OpenWeatherSpider', 1, '["weather", "climate", "temperature"]', 3600, 1),
(30, 'Open-Meteo开源天气', 'monitoring', 'https://api.open-meteo.com/v1/forecast', 'OpenMeteoSpider', 1, '["weather", "forecast", "climate"]', 3600, 1),
(31, 'NASA POWER气象数据', 'monitoring', 'https://power.larc.nasa.gov/api/temporal/daily/point', 'NASAPOWERSpider', 0, '["solar", "meteorological", "climate"]', 86400, 1),
(32, '中国空气质量数据', 'monitoring', 'https://aqicn.org/data-platform/register/', 'AQICNSpider', 0, '["AQI", "PM2.5", "air quality"]', 3600, 1),
(33, 'Nominatim地理编码', 'monitoring', 'https://nominatim.openstreetmap.org/search', 'NominatimSpider', 1, '["geocoding", "location", "coordinates"]', 604800, 1),
(34, 'Open-Meteo地理编码', 'monitoring', 'https://geocoding-api.open-meteo.com/v1/search', 'OpenMeteoGeocodingSpider', 1, '["city", "location", "search"]', 604800, 1),
(35, 'Reddit科技讨论', 'social', 'https://www.reddit.com/r/technology', 'RedditSpider', 0, '["earthquake", "disaster", "seismic"]', 1800, 1),
(36, 'Reddit科学讨论', 'social', 'https://www.reddit.com/r/science', 'RedditScienceSpider', 0, '["earthquake", "geology", "seismology"]', 1800, 1);
