# IntelliKnow 数据源配置指南

本文档汇总了 IntelliKnow 系统支持的所有数据源，按类别分组。

---

## 1. 地震监测 (Earthquake Monitoring)

| 数据源名称 | API地址 | 说明 | 状态 |
|-----------|---------|------|------|
| **USGS全球地震目录** | `https://earthquake.usgs.gov/fdsnws/event/1/query` | 美国地质调查局，全球地震数据 | ✅ 已启用 |
| **中国地震台网** | `https://data.earthquake.cn/datashare/globeEarthquake_csn` | 中国地震台网中心 | ✅ 已启用 |
> **⚠️ 特殊配置说明**: 中国地震台网有两个可用接口：
> 1. `data.earthquake.cn` (优先) - FDSN 标准接口，支持 HTTPS
> 2. `ceic.ac.cn` (备选) - 旧接口，必须使用 HTTP，需要设置 Referer 头，处理 GBK 编码
| **EMSC欧洲地中海地震中心** | `https://www.seismicportal.eu/fdsnws/event/1/query` | 欧洲地中海地区地震 | ✅ 已启用 |
| **ISC国际地震中心** | `https://www.isc.ac.uk/fdsnws/event/1/query` | 国际地震目录 | ✅ 已启用 |
| **GCMT全球矩心矩张量** | `https://www.globalcmt.org/cgi/globalcmt-cgi-bin/CMT5/form` | 震源机制解 | ✅ 已启用 |
| **FNET日本地震海啸监测** | `https://www.fnet.bosai.go.jp/` | 日本地震海啸监测 | ❌ 已禁用 |

---

## 2. 学术文献 (Academic)

| 数据源名称 | API地址 | 说明 | 状态 |
|-----------|---------|------|------|
| **arXiv** | `http://export.arxiv.org/api/query` | 预印本服务器，物理学、地球物理学期刊 | ✅ 已启用 |
| **Semantic Scholar** | `https://api.semanticscholar.org/graph/v1/paper/search` | AI驱动的学术搜索，2.25亿+论文 | ✅ 已启用 |
| **OpenAlex** | `https://api.openalex.org/works` | 开放的学术知识库，3亿+学术作品 | ✅ 已启用 |
| **CrossRef** | `https://api.crossref.org/works` | DOI元数据，2万+出版商 | ✅ 已启用 |
| **PubMed** | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` | 医学文献数据库 | ❌ 已禁用 |
| **CORE** | `https://api.core.ac.uk/v3/search/works` | 开放获取论文聚合 | ✅ 已启用 |
| **SciTeX Scholar** | `https://scitex.ai/docs/web-api/scholar-api/` | 综合学术搜索API | 需配置 |

### 学术API申请方式

```python
# OpenAlex - 完全免费
# 访问: https://openalex.org/settings/api
# 获取免费的API Key

# Semantic Scholar - 免费但需申请
# 访问: https://www.semanticscholar.org/faq/public-api
# 申请API Key

# CrossRef - 免费使用
# 访问: https://www.crossref.org/categories/api/
# 注册获取Token

# arXiv - 完全免费
# 无需API Key，直接使用
```

---

## 3. 专利 (Patent)

| 数据源名称 | API地址 | 说明 | 状态 |
|-----------|---------|------|------|
| **USPTO** | `https://developer.uspto.gov/api/v1/patents` | 美国专利商标局 | ✅ 已启用 |
| **EPO** | `https://ops.epo.org/3.2/rest-services/` | 欧洲专利局 | ✅ 已启用 |
| **Google Patents** | `https://patents.google.com/xhr/query` | 谷歌专利搜索 | ✅ 已启用 |
| **WIPO** | `https://patentscope.wipo.int/search/en/search.jsf` | 世界知识产权组织 | ❌ 已禁用 |
| **CNIPA** | `https://pss-system.cponline.cnipa.gov.cn` | 中国国家知识产权局 | ✅ 已启用 |

### 专利API申请方式

```python
# USPTO - 免费
# 访问: https://developer.uspto.gov/
# 注册账户获取API Key

# EPO Open Patent Services - 免费
# 访问: https://www.epo.org/ops
# 注册获取API Key（每周4GB免费额度）

# Google Patents - 爬虫方式
# 无需API，直接爬取

# CNIPA - 需注册
# 访问: https://www.cnipa.gov.cn/
# 注册企业账号获取接口权限
```

---

## 4. 新闻 (News)

| 数据源名称 | API地址 | 说明 | 状态 |
|-----------|---------|------|------|
| **应急管理部** | `https://www.mem.gov.cn/xw/zhsgxx` | 中国应急管理部官网 | ✅ 已启用 |
| **中国地震局** | `http://www.cea.gov.cn/cea/xwzx/zyzt/index.html` | 中国地震局官网 | ✅ 已启用 |
| **NewsAPI** | `https://newsapi.org/v2/everything` | 全球新闻聚合API | ✅ 已启用 |
| **中国地震台网速报** | `https://news.ceic.ac.cn/` | 地震速报新闻 | ✅ 已启用 |
| **新华网RSS** | `http://www.news.cn/rss/tech.xml` | 新华网科技RSS | ✅ 已启用 |
| **人民网RSS** | `http://paper.people.com.cn/rss/technology.xml` | 人民网科技RSS | ✅ 已启用 |

### 新闻API申请方式

```python
# NewsAPI - 免费版
# 访问: https://newsapi.org/
# 注册获取免费API Key（开发环境免费）

# World News API - 免费
# 访问: https://worldnewsapi.com/
# 注册获取免费API Key

# The News API
# 访问: https://www.thenewsapi.com/
# 注册获取免费API Key
```

---

## 5. 政府数据 (Government)

| 数据源名称 | API地址 | 说明 | 状态 |
|-----------|---------|------|------|
| **World Bank** | `https://api.worldbank.org/v2` | 世界银行发展指标 | ✅ 已启用 |
| **OECD** | `https://stats.oecd.org/SDMX-JSON/data` | 经合组织统计数据 | ❌ 已禁用 |
| **中国国家统计局** | `https://data.stats.gov.cn/easyquery.htm` | 中国统计数据 | ❌ 已禁用 |

### 政府API申请方式

```python
# World Bank - 完全免费
# 无需API Key，直接访问

# OECD - 免费但需注册
# 访问: https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html
# 遵守使用条款

# FRED (美联储经济数据) - 免费
# 访问: https://fred.stlouisfed.org/docs/api/fred/
# 注册获取API Key
```

---

## 6. 金融经济 (Financial)

| 数据源名称 | API地址 | 说明 | 状态 |
|-----------|---------|------|------|
| **FRED** | `https://api.stlouisfed.org/fred/series/observations` | 美联储经济数据 | ✅ 已启用 |
| **Alpha Vantage** | `https://www.alphavantage.co/query` | 股票、外汇、商品数据 | ❌ 已禁用 |

### 金融API申请方式

```python
# Alpha Vantage - 免费
# 访问: https://www.alphavantage.co/
# 注册获取免费API Key（每天5次请求）

# FRED - 免费
# 访问: https://fred.stlouisfed.org/
# 注册获取API Key（可选，用于更多功能）
```

---

## 7. 气象环境 (Weather/Environment)

| 数据源名称 | API地址 | 说明 | 状态 |
|-----------|---------|------|------|
| **OpenWeatherMap** | `https://api.openweathermap.org/data/2.5/weather` | 天气预报数据 | ✅ 已启用 |
| **Open-Meteo** | `https://api.open-meteo.com/v1/forecast` | 开源天气API | ✅ 已启用 |
| **NASA POWER** | `https://power.larc.nasa.gov/api/temporal/daily/point` | NASA气象卫星数据 | ❌ 已禁用 |
| **中国空气质量** | `https://aqicn.org/data-platform/register/` | AQI空气质量数据 | ❌ 已禁用 |

### 气象API申请方式

```python
# OpenWeatherMap - 免费
# 访问: https://openweathermap.org/api
# 注册获取免费API Key

# Open-Meteo - 完全免费
# 无需API Key，直接使用

# NASA POWER - 完全免费
# 无需API Key，直接访问

# AQI.CN - 免费
# 访问: https://aqicn.org/data-platform/
# 注册获取Token
```

---

## 8. 地理编码 (Geocoding)

| 数据源名称 | API地址 | 说明 | 状态 |
|-----------|---------|------|------|
| **Nominatim** | `https://nominatim.openstreetmap.org/search` | OpenStreetMap地理编码 | ✅ 已启用 |
| **Open-Meteo Geocoding** | `https://geocoding-api.open-meteo.com/v1/search` | 位置名称搜索 | ✅ 已启用 |

### 地理编码API申请方式

```python
# Nominatim - 免费但需遵守使用政策
# 无需API Key
# 重要: 遵守使用政策，每秒最多1个请求

# Open-Meteo Geocoding - 完全免费
# 无需API Key
```

---

## 9. 社交媒体 (Social)

| 数据源名称 | API地址 | 说明 | 状态 |
|-----------|---------|------|------|
| **Reddit科技** | `https://www.reddit.com/r/technology` | Reddit科技讨论 | ❌ 已禁用 |
| **Reddit科学** | `https://www.reddit.com/r/science` | Reddit科学讨论 | ❌ 已禁用 |

### 社交媒体API申请方式

```python
# Reddit - 需要申请
# 访问: https://www.reddit.com/dev/api/
# 注册开发者应用获取API Key
# 注意: Reddit API已改为付费模式

# Pushshift - 限流
# 访问: https://api.pushshift.io/
# 仅限Reddit版主使用
```

---

## 10. 空间科学 (Space Science)

| 数据源名称 | API地址 | 说明 | 状态 |
|-----------|---------|------|------|
| **NASA Heliophysics** | `https://heliophysicsdata.gsfc.nasa.gov/WebServices/` | 空间物理数据 | 待添加 |
| **太阳活动数据** | `https://api.solarmonitor.org/` | 太阳黑子、耀斑数据 | 待添加 |

---

## 更新日志

| 日期 | 更新内容 |
|------|---------|
| 2026-05-04 | 初始化数据源配置，从6个扩展到40+个数据源 |
