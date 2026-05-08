"""USGS Earthquake Spider."""
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Optional
from apps.crawlers.base import BaseSpider, SpiderConfig, EarthquakeEventData
import logging

logger = logging.getLogger(__name__)


class USGSSpider(BaseSpider):
    """USGS Earthquake Catalog Spider.

    API Documentation: https://earthquake.usgs.gov/fdsnws/event/1/
    """

    def __init__(self, config: SpiderConfig = None):
        super().__init__(config or SpiderConfig())
        self.base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    async def search(
        self,
        query: str = "",
        starttime: datetime = None,
        endtime: datetime = None,
        minmagnitude: float = 4.0,
        format: str = "geojson"
    ) -> List[EarthquakeEventData]:
        """Search earthquake events from USGS."""
        if not starttime:
            starttime = datetime.utcnow() - timedelta(days=7)
        if not endtime:
            endtime = datetime.utcnow()

        params = {
            "format": format,
            "starttime": starttime.strftime("%Y-%m-%d"),
            "endtime": endtime.strftime("%Y-%m-%d"),
            "minmagnitude": minmagnitude,
            "orderby": "time"
        }

        url = self.base_url
        if format == "geojson":
            url += "?format=geojson"
            params_str = "&".join([f"{k}={v}" for k, v in params.items() if k != "format"])
            url += "&" + params_str
        else:
            params_str = "&".join([f"{k}={v}" for k, v in params.items()])

        try:
            response = await self._fetch_with_retry(url)
            if not response:
                return []

            data = response.json()
            features = data.get("features", [])

            events = []
            for feature in features:
                props = feature.get("properties", {})
                geometry = feature.get("geometry", {})

                event = EarthquakeEventData(
                    event_id=feature.get("id", ""),
                    magnitude=props.get("mag", 0) or 0,
                    latitude=geometry.get("coordinates", [0, 0, 0])[1] if geometry else 0,
                    longitude=geometry.get("coordinates", [0, 0, 0])[0] if geometry else 0,
                    depth=geometry.get("coordinates", [0, 0, 0])[2] if geometry else 0,
                    location=props.get("place", ""),
                    region=self._extract_region(props.get("place", "")),
                    time=datetime.fromtimestamp(props.get("time", 0) / 1000) if props.get("time") else None,
                    source="USGS"
                )
                events.append(event)

            logger.info(f"[USGSSpider] Fetched {len(events)} earthquake events")
            return events

        except Exception as e:
            logger.error(f"[USGSSpider] Error: {e}")
            return []

    async def fetch_article(self, article_id: str) -> Optional[EarthquakeEventData]:
        """Fetch single earthquake event details."""
        url = f"https://earthquake.usgs.gov/fdsnws/event/1/detail/{article_id}?format=geojson"
        try:
            response = await self._fetch_with_retry(url)
            if not response:
                return None

            data = response.json()
            props = data.get("properties", {})
            geometry = data.get("geometry", {})

            return EarthquakeEventData(
                event_id=data.get("id", ""),
                magnitude=props.get("mag", 0) or 0,
                latitude=geometry.get("coordinates", [0, 0, 0])[1] if geometry else 0,
                longitude=geometry.get("coordinates", [0, 0, 0])[0] if geometry else 0,
                depth=geometry.get("coordinates", [0, 0, 0])[2] if geometry else 0,
                location=props.get("place", ""),
                region=self._extract_region(props.get("place", "")),
                time=datetime.fromtimestamp(props.get("time", 0) / 1000) if props.get("time") else None,
                source="USGS"
            )
        except Exception as e:
            logger.error(f"[USGSSpider] Error fetching event {article_id}: {e}")
            return None

    def _extract_region(self, place: str) -> str:
        """Extract region/country from place string."""
        if not place:
            return ""
        parts = place.split(",")
        if len(parts) > 1:
            return parts[-1].strip()
        return ""


class ChinaEarthquakeSpider(BaseSpider):
    """China Earthquake Spider using CENC (China Earthquake Networks Center) API.

    使用中国地震台网官方 API: https://www.cenc.ac.cn
    数据来源: 中国地震台网中心 (CENC)
    """

    def __init__(self, config: SpiderConfig = None):
        super().__init__(config or SpiderConfig())
        self.base_url = "https://www.cenc.ac.cn/prodlaunch-web-backend/open/data/catalogs"

    async def search(
        self,
        query: str = "",
        starttime: datetime = None,
        endtime: datetime = None,
        minmagnitude: float = 3.0
    ) -> List[EarthquakeEventData]:
        """Search earthquake events from CENC API."""
        if not starttime:
            starttime = datetime.utcnow() - timedelta(days=30)
        if not endtime:
            endtime = datetime.utcnow()
        
        # 转换时区: UTC -> 北京时间 (CENC API 使用北京时间)
        starttime_local = starttime + timedelta(hours=8)
        endtime_local = endtime + timedelta(hours=8)

        events = []
        try:
            url = (
                f"{self.base_url}?orderBy=id&isAsc=false"
                f"&startMg={minmagnitude}&endMg=10"
                f"&startTime={starttime_local.strftime('%Y-%m-%d+%H:%M:%S')}"
                f"&endTime={endtime_local.strftime('%Y-%m-%d+%H:%M:%S')}"
                f"&locationRange=1"
            )

            response = await self._fetch_with_retry(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Referer": "https://www.cenc.ac.cn/earthquake-manage-publish-web/search",
                }
            )
            if not response:
                logger.warning("[ChinaEarthquakeSpider] No response from CENC API")
                return []

            data = response.json()
            if data.get("code") != 0:
                logger.warning(f"[ChinaEarthquakeSpider] CENC API error: {data.get('message')}")
                return []

            items = data.get("data", [])
            
            for item in items:
                # 解析发震时间
                # oriTime 可能是字符串 "2026-05-08 14:42:13" (北京时间) 或毫秒时间戳
                ori_time = item.get("oriTime")
                if isinstance(ori_time, str):
                    # 字符串时间格式: "2026-05-08 14:42:13" (北京时间)
                    try:
                        event_time = datetime.strptime(ori_time, "%Y-%m-%d %H:%M:%S") - timedelta(hours=8)
                    except:
                        event_time = None
                elif isinstance(ori_time, (int, float)) and ori_time > 0:
                    # 毫秒时间戳
                    event_time = datetime.fromtimestamp(ori_time / 1000) - timedelta(hours=8)
                else:
                    event_time = None

                event = EarthquakeEventData(
                    event_id=str(item.get("uniEventId", "")),
                    magnitude=float(item.get("magnitude", 0) or 0),
                    latitude=float(item.get("epiLat", 0) or 0),
                    longitude=float(item.get("epiLon", 0) or 0),
                    depth=float(item.get("focDepth", 0) or 0),
                    location=item.get("locName", ""),
                    region="China",
                    time=event_time,
                    source="中国地震台网"
                )
                events.append(event)

            logger.info(f"[ChinaEarthquakeSpider] Fetched {len(events)} events from CENC API")
            return events

        except Exception as e:
            logger.error(f"[ChinaEarthquakeSpider] Error: {e}")
            return []

    async def fetch_article(self, article_id: str) -> Optional[EarthquakeEventData]:
        """Fetch single earthquake event details."""
        return None


class EMSCSpider(BaseSpider):
    """European-Mediterranean Seismological Centre Spider."""

    def __init__(self, config: SpiderConfig = None):
        super().__init__(config or SpiderConfig())
        self.base_url = "https://www.seismicportal.eu/fdsnws/event/1/query"

    async def search(
        self,
        query: str = "",
        starttime: datetime = None,
        endtime: datetime = None,
        minmagnitude: float = 4.0,
        format: str = "xml"  # 默认使用 XML 格式，geojson 不稳定
    ) -> List[EarthquakeEventData]:
        """Search earthquake events from EMSC."""
        if not starttime:
            starttime = datetime.utcnow() - timedelta(days=7)
        if not endtime:
            endtime = datetime.utcnow()

        url = f"{self.base_url}?format={format}&starttime={starttime.strftime('%Y-%m-%d')}&endtime={endtime.strftime('%Y-%m-%d')}&minmagnitude={minmagnitude}"

        try:
            response = await self._fetch_with_retry(url)
            if not response:
                return []

            events = []

            if format == "xml":
                # 解析 XML 格式
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)

                # 命名空间
                ns = {
                    "q": "http://quakeml.org/xmlns/quakeml/1.2",
                    "bed": "http://quakeml.org/xmlns/bed/1.2"
                }

                for event in root.findall(".//bed:event", ns):
                    desc_elem = event.find("bed:description/bed:text", ns)
                    description = desc_elem.text if desc_elem is not None else ""

                    origin = event.find("bed:preferredOriginID/..", ns)
                    if origin is None:
                        # 尝试其他方式获取 origin
                        origin = event.find(".//bed:origin", ns)

                    if origin is not None:
                        time_elem = origin.find("bed:time/bed:value", ns)
                        lat_elem = origin.find("bed:latitude/bed:value", ns)
                        lon_elem = origin.find("bed:longitude/bed:value", ns)
                        depth_elem = origin.find("bed:depth/bed:value", ns)

                        time_str = time_elem.text if time_elem is not None else None
                        lat = float(lat_elem.text) if lat_elem is not None else 0
                        lon = float(lon_elem.text) if lon_elem is not None else 0
                        depth = float(depth_elem.text) / 1000 if depth_elem is not None else 0  # 转换为 km

                        mag_elem = event.find(".//bed:magnitude/bed:mag/bed:value", ns)
                        mag = float(mag_elem.text) if mag_elem is not None else 0

                        event_elem = EarthquakeEventData(
                            event_id=event.get("publicID", ""),
                            magnitude=mag,
                            latitude=lat,
                            longitude=lon,
                            depth=depth,
                            location=description,
                            region="",
                            time=datetime.fromisoformat(time_str.replace("Z", "+00:00")) if time_str else None,
                            source="EMSC"
                        )
                        events.append(event_elem)
            else:
                # geojson 格式
                data = response.json()
                features = data.get("features", [])

                for feature in features:
                    props = feature.get("properties", {})
                    geometry = feature.get("geometry", {})

                    event = EarthquakeEventData(
                        event_id=feature.get("id", ""),
                        magnitude=props.get("mag", 0) or 0,
                        latitude=geometry.get("coordinates", [0, 0, 0])[1] if geometry else 0,
                        longitude=geometry.get("coordinates", [0, 0, 0])[0] if geometry else 0,
                        depth=geometry.get("coordinates", [0, 0, 0])[2] if geometry else 0,
                        location=props.get("flyght_locality", "") or props.get("place", ""),
                        region=props.get("flyght_region", "") or "",
                        time=datetime.fromisoformat(props.get("time", "").replace("Z", "+00:00")) if props.get("time") else None,
                        source="EMSC"
                    )
                    events.append(event)

            logger.info(f"[EMSCSpider] Fetched {len(events)} events")
            return events

        except Exception as e:
            logger.error(f"[EMSCSpider] Error: {e}")
            return []

    async def fetch_article(self, article_id: str) -> Optional[EarthquakeEventData]:
        """Fetch single earthquake event details."""
        url = f"{self.base_url}/{article_id}?format=xml"
        try:
            response = await self._fetch_with_retry(url)
            if not response:
                return None

            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.text)

            ns = {
                "q": "http://quakeml.org/xmlns/quakeml/1.2",
                "bed": "http://quakeml.org/xmlns/bed/1.2"
            }

            event = root.find(".//bed:event", ns)
            if event is None:
                return None

            desc_elem = event.find("bed:description/bed:text", ns)
            description = desc_elem.text if desc_elem is not None else ""

            origin = event.find(".//bed:origin", ns)

            time_elem = origin.find("bed:time/bed:value", ns)
            lat_elem = origin.find("bed:latitude/bed:value", ns)
            lon_elem = origin.find("bed:longitude/bed:value", ns)
            depth_elem = origin.find("bed:depth/bed:value", ns)

            time_str = time_elem.text if time_elem is not None else None
            lat = float(lat_elem.text) if lat_elem is not None else 0
            lon = float(lon_elem.text) if lon_elem is not None else 0
            depth = float(depth_elem.text) / 1000 if depth_elem is not None else 0

            mag_elem = event.find(".//bed:magnitude/bed:mag/bed:value", ns)
            mag = float(mag_elem.text) if mag_elem is not None else 0

            return EarthquakeEventData(
                event_id=event.get("publicID", ""),
                magnitude=mag,
                latitude=lat,
                longitude=lon,
                depth=depth,
                location=description,
                region="",
                time=datetime.fromisoformat(time_str.replace("Z", "+00:00")) if time_str else None,
                source="EMSC"
            )
        except Exception as e:
            logger.error(f"[EMSCSpider] Error fetching event {article_id}: {e}")
            return None
