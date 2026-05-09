"""Translation service for academic papers - supports multiple providers with fallback.

Design patterns used:
- Strategy Pattern: Each translation provider is a separate strategy
- Factory Pattern: TranslationProviderFactory creates providers
- Template Method Pattern: Base class defines translation workflow

Supported Providers:
  FREE (no API key): gemma, mymemory
  DOMESTIC (paid):   baidu, tencent, youdao
  FOREIGN (paid):    deepl, google
"""
import os
import re
import hashlib
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
import httpx

logger = logging.getLogger(__name__)

# Short timeouts for fast fallback
DEFAULT_TIMEOUT = 10  # seconds


# ==================== Strategy Interface ====================

class TranslationProvider(ABC):
    """Abstract base class for all translation providers (Strategy Pattern)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        pass

    @property
    def is_domestic(self) -> bool:
        """Whether this is a domestic (China) provider."""
        return True

    @abstractmethod
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        """Translate text. Returns None if translation fails."""
        pass

    def is_available(self) -> bool:
        """Check if provider has valid credentials."""
        return True


# ==================== Free Domestic Providers (No API key required) ====================

class GemmaProvider(TranslationProvider):
    """Gemma Translate - Free AI translation, no API key required."""

    @property
    def name(self) -> str:
        return "gemma"

    @property
    def is_domestic(self) -> bool:
        return True

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        lang_map = {"en": "english", "zh": "chinese", "zh-CN": "chinese"}
        source = lang_map.get(source_lang, source_lang)
        target = lang_map.get(target_lang, target_lang)

        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.post(
                    "https://api.gemmatranslate.org/translate",
                    json={
                        "text": text[:5000],
                        "source": source,
                        "target": target
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("translated_text", "")
                return None
        except Exception as e:
            logger.warning(f"Gemma translation failed: {e}")
            raise


class MyMemoryProvider(TranslationProvider):
    """MyMemory Translation API - free, no key, rate limited."""

    @property
    def name(self) -> str:
        return "mymemory"

    @property
    def is_domestic(self) -> bool:
        return True  # Generally accessible

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        max_chunk_size = 400
        target_pair = f"{source_lang}|{target_lang}"

        paragraphs = re.split(r'\n\s*\n', text)
        translated_parts = []

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            for paragraph in paragraphs:
                if not paragraph.strip():
                    translated_parts.append("")
                    continue

                sentences = re.split(r'(?<=[.!?。！？])\s+', paragraph)
                current_chunk = []

                for sentence in sentences:
                    current_text = " ".join(current_chunk)
                    estimated_len = len(current_text) * 0.7

                    if estimated_len + len(sentence) > max_chunk_size and current_chunk:
                        chunk_text = " ".join(current_chunk)
                        translated = await self._translate_single(chunk_text, target_pair, client)
                        if translated:
                            translated_parts.append(translated)
                        current_chunk = [sentence]
                    else:
                        current_chunk.append(sentence)

                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    translated = await self._translate_single(chunk_text, target_pair, client)
                    if translated:
                        translated_parts.append(translated)

        result = "\n\n".join(translated_parts)
        return result if result.strip() else None

    async def _translate_single(
        self,
        text: str,
        lang_pair: str,
        client: httpx.AsyncClient
    ) -> Optional[str]:
        if not text.strip():
            return ""

        try:
            response = await client.get(
                "https://api.mymemory.translated.net/get",
                params={"q": text, "langpair": lang_pair}
            )
            data = response.json()
            if data.get("responseStatus") == 200:
                return data.get("responseData", {}).get("translatedText", "")
            elif data.get("responseStatus") == 429:
                logger.warning("MyMemory rate limited")
                raise Exception("MyMemory rate limited")
        except Exception as e:
            raise


# ==================== Paid Domestic Providers ====================

class BaiduProvider(TranslationProvider):
    """Baidu Translation API (domestic)."""

    def __init__(self):
        self.appid = os.getenv("BAIDU_TRANSLATE_APPID", "")
        self.secret = os.getenv("BAIDU_TRANSLATE_SECRET", "")

    @property
    def name(self) -> str:
        return "baidu"

    @property
    def is_domestic(self) -> bool:
        return True

    def is_available(self) -> bool:
        return bool(self.appid and self.secret)

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        if not self.is_available():
            return None

        try:
            salt = str(int(time.time()))
            sign_str = f"{self.appid}{text[:500]}{salt}{self.secret}"
            sign = hashlib.md5(sign_str.encode()).hexdigest()

            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.get(
                    "https://fanyi-api.baidu.com/api/trans/vip/translate",
                    params={
                        "q": text[:5000],
                        "appid": self.appid,
                        "salt": salt,
                        "from": source_lang,
                        "to": target_lang,
                        "sign": sign
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if "trans_result" in data and data["trans_result"]:
                        return "".join(t.get("dst", "") for t in data["trans_result"])
                    elif "error_code" in data:
                        logger.warning(f"Baidu API error: {data.get('error_msg', data['error_code'])}")
                return None
        except Exception as e:
            logger.warning(f"Baidu translation failed: {e}")
            raise


class TencentProvider(TranslationProvider):
    """Tencent Cloud Translation API (domestic)."""

    def __init__(self):
        self.secret_id = os.getenv("TENCENT_SECRET_ID", "")
        self.secret_key = os.getenv("TENCENT_SECRET_KEY", "")

    @property
    def name(self) -> str:
        return "tencent"

    @property
    def is_domestic(self) -> bool:
        return True

    def is_available(self) -> bool:
        return bool(self.secret_id and self.secret_key)

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        if not self.is_available():
            return None

        import base64
        import hmac
        from datetime import datetime, timezone

        try:
            service = "tmt"
            host = "tmt.tencentcloudapi.com"
            endpoint = f"https://{host}"
            region = os.getenv("TENCENT_REGION", "ap-guangzhou")
            action = "TextTranslate"
            version = "2018-03-21"

            payload = {
                "SourceText": text[:5000],
                "Source": source_lang,
                "Target": target_lang,
                "ProjectId": 0
            }

            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Host": host,
                        "X-TC-Action": action,
                        "X-TC-Version": version,
                        "X-TC-Region": region
                    },
                    params={
                        "Action": action,
                        "Version": version,
                        "Region": region,
                        "SecretId": self.secret_id,
                        "Timestamp": int(time.time()),
                        "Nonce": int(time.time() % 100000)
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if "Response" in data and "TargetText" in data["Response"]:
                        return data["Response"]["TargetText"]
                return None
        except Exception as e:
            logger.warning(f"Tencent translation failed: {e}")
            raise


class YoudaoProvider(TranslationProvider):
    """Youdao Translation API (domestic)."""

    def __init__(self):
        self.appkey = os.getenv("YOUDAO_APPKEY", "")
        self.appsecret = os.getenv("YOUDAO_APPSECRET", "")

    @property
    def name(self) -> str:
        return "youdao"

    @property
    def is_domestic(self) -> bool:
        return True

    def is_available(self) -> bool:
        return bool(self.appkey and self.appsecret)

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        if not self.is_available():
            return None

        import uuid

        try:
            truncate_text = text[:5000] if len(text) > 5000 else text

            data = {
                "q": truncate_text,
                "from": source_lang,
                "to": target_lang
            }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.post(
                    "https://openapi.youdao.com/api",
                    data=data,
                    headers=headers
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("errorCode") == "0" and "translation" in result:
                        return result["translation"][0] if result["translation"] else None
                return None
        except Exception as e:
            logger.warning(f"Youdao translation failed: {e}")
            raise


# ==================== Paid Foreign Providers ====================

class DeepLProvider(TranslationProvider):
    """DeepL Translation API (foreign)."""

    def __init__(self):
        self.api_key = os.getenv("DEEPL_API_KEY", "")

    @property
    def name(self) -> str:
        return "deepl"

    @property
    def is_domestic(self) -> bool:
        return False

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        if not self.is_available():
            return None

        try:
            deepl_target = "ZH" if target_lang == "zh" else target_lang.upper()

            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.post(
                    "https://api-free.deepl.com/v2/translate"
                    if "free" in self.api_key.lower()
                    else "https://api.deepl.com/v2/translate",
                    data={
                        "auth_key": self.api_key,
                        "text": text[:5000],
                        "target_lang": deepl_target
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("translations", [{}])[0].get("text", "")
                return None
        except Exception as e:
            logger.warning(f"DeepL translation failed: {e}")
            raise


class GoogleProvider(TranslationProvider):
    """Google Translate API (foreign, may be blocked in China)."""

    @property
    def name(self) -> str:
        return "google"

    @property
    def is_domestic(self) -> bool:
        return False

    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.get(
                    "https://translate.googleapis.com/translate_a/single",
                    params={
                        "client": "gtx",
                        "sl": source_lang,
                        "tl": target_lang,
                        "dt": "t",
                        "q": text[:5000]
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    if data and data[0]:
                        return "".join(part[0] for part in data[0] if part[0])
                return None
        except Exception as e:
            logger.warning(f"Google translation failed: {e}")
            raise


# ==================== Factory ====================

class TranslationProviderFactory:
    """Factory for creating translation providers (Factory Pattern)."""

    _provider_classes = {
        # Free (no API key)
        "gemma": GemmaProvider,
        "mymemory": MyMemoryProvider,
        # Paid domestic
        "baidu": BaiduProvider,
        "tencent": TencentProvider,
        "youdao": YoudaoProvider,
        # Paid foreign
        "deepl": DeepLProvider,
        "google": GoogleProvider,
    }

    @classmethod
    def create(cls, provider_name: str) -> Optional[TranslationProvider]:
        """Create a provider instance by name."""
        provider_class = cls._provider_classes.get(provider_name.lower())
        if provider_class:
            return provider_class()
        return None

    @classmethod
    def create_all(cls) -> List[TranslationProvider]:
        """Create all available provider instances."""
        return [cls.create(name)() for name in cls._provider_classes]

    @classmethod
    def register(cls, name: str, provider_class: type):
        """Register a new provider (extensibility)."""
        cls._provider_classes[name.lower()] = provider_class


# ==================== Translation Service ====================

class TranslationService:
    """Translation service with automatic fallback (Template Method Pattern)."""

    # Priority: free domestic -> paid domestic -> foreign
    DEFAULT_DOMESTIC_ORDER = ["gemma", "mymemory", "baidu", "tencent", "youdao"]
    DEFAULT_FOREIGN_ORDER = ["deepl", "google"]

    def __init__(self):
        self.primary_provider = os.getenv("TRANSLATION_PROVIDER", "gemma").lower()
        self._providers: List[TranslationProvider] = []
        self._domestic_providers: List[TranslationProvider] = []
        self._foreign_providers: List[TranslationProvider] = []
        self._init_providers()

    def _init_providers(self):
        """Initialize all providers and categorize them."""
        all_provider_names = self.DEFAULT_DOMESTIC_ORDER + self.DEFAULT_FOREIGN_ORDER

        for name in all_provider_names:
            provider = TranslationProviderFactory.create(name)
            if provider and provider.is_available():
                if provider.is_domestic:
                    self._domestic_providers.append(provider)
                else:
                    self._foreign_providers.append(provider)

        # Build ordered list: primary -> domestic -> foreign
        self._providers = []
        primary = TranslationProviderFactory.create(self.primary_provider)
        if primary and primary.is_available():
            self._providers.append(primary)

        for p in self._domestic_providers:
            if p.name != self.primary_provider:
                self._providers.append(p)

        for p in self._foreign_providers:
            if p.name != self.primary_provider:
                self._providers.append(p)

        logger.info(f"Translation providers loaded: {[p.name for p in self._providers]}")

    def _get_language_pair(self, to_chinese: bool) -> Tuple[str, str]:
        """Get source and target language codes."""
        if to_chinese:
            return ("en", "zh")
        return ("zh", "en")

    def _is_target_language(self, text: str, to_chinese: bool) -> bool:
        """Check if text is already in the target language."""
        if to_chinese:
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            return len(text) > 0 and chinese_chars / len(text) > 0.5
        else:
            english_chars = sum(1 for c in text if c.isascii())
            return len(text) > 0 and english_chars / len(text) > 0.8

    async def translate_to_chinese(self, text: str) -> Optional[str]:
        """Translate text to Chinese with fallback."""
        return await self._translate(text, to_chinese=True)

    async def translate_to_english(self, text: str) -> Optional[str]:
        """Translate text to English with fallback."""
        return await self._translate(text, to_chinese=False)

    async def _translate(self, text: str, to_chinese: bool) -> Optional[str]:
        """Template method for translation workflow."""
        if not text or not text.strip():
            return ""

        # Skip if already in target language
        if self._is_target_language(text, to_chinese):
            return text

        source_lang, target_lang = self._get_language_pair(to_chinese)
        last_error = None

        for provider in self._providers:
            try:
                logger.info(f"Trying translation provider: {provider.name}")
                result = await provider.translate(text, source_lang, target_lang)

                if result:
                    logger.info(f"Translation successful with {provider.name}")
                    return result
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue

        logger.error(f"All translation providers failed. Last error: {last_error}")
        return None


# Singleton instance
translation_service = TranslationService()
