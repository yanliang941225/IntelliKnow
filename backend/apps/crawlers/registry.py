"""Spider registry and factory."""
from typing import Dict, Type, Optional
from apps.crawlers.base import BaseSpider, SpiderConfig, Article, EarthquakeEventData


SPIDER_REGISTRY: Dict[str, Type[BaseSpider]] = {}


def register_spider(name: str, spider_class: Type[BaseSpider]):
    """Register a spider class."""
    SPIDER_REGISTRY[name] = spider_class


def get_spider(name: str, config: SpiderConfig = None) -> Optional[BaseSpider]:
    """Get spider instance by name."""
    spider_class = SPIDER_REGISTRY.get(name)
    if spider_class:
        return spider_class(config)
    return None


def list_spiders() -> Dict[str, Type[BaseSpider]]:
    """List all registered spiders."""
    return SPIDER_REGISTRY.copy()


def init_registry():
    """Initialize spider registry with all available spiders."""
    from apps.crawlers.spiders.earthquake_spiders import USGSSpider, ChinaEarthquakeSpider, EMSCSpider
    from apps.crawlers.spiders.academic_spiders import ArxivSeismologySpider, SemanticScholarSpider, OpenAlexSpider
    from apps.crawlers.spiders.news_spiders import EmergencyNewsSpider, RSSNewsSpider

    register_spider("USGSSpider", USGSSpider)
    register_spider("ChinaEarthquakeSpider", ChinaEarthquakeSpider)
    register_spider("EMSCSpider", EMSCSpider)
    register_spider("ArxivSeismologySpider", ArxivSeismologySpider)
    register_spider("SemanticScholarSpider", SemanticScholarSpider)
    register_spider("OpenAlexSpider", OpenAlexSpider)
    register_spider("EmergencyNewsSpider", EmergencyNewsSpider)
    register_spider("RSSNewsSpider", RSSNewsSpider)


__all__ = [
    "BaseSpider",
    "SpiderConfig",
    "Article",
    "EarthquakeEventData",
    "register_spider",
    "get_spider",
    "list_spiders",
    "init_registry"
]
