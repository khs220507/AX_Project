"""Google News RSS 크롤링 서비스 (무료, API 키 불필요)"""

import time
import logging
import hashlib
import re
from urllib.parse import quote
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# 뉴스 결과 캐시 (TTL 1시간)
_news_cache: dict[str, tuple[float, list[dict]]] = {}
NEWS_CACHE_TTL = 3600


def _cache_key(query: str) -> str:
    return hashlib.md5(query.encode()).hexdigest()


def _get_cached(query: str) -> list[dict] | None:
    key = _cache_key(query)
    if key in _news_cache:
        expire, data = _news_cache[key]
        if time.time() < expire:
            return data
        del _news_cache[key]
    return None


def _set_cached(query: str, data: list[dict]):
    _news_cache[_cache_key(query)] = (time.time() + NEWS_CACHE_TTL, data)


def _clean_html(html: str) -> str:
    """HTML 태그 제거"""
    return re.sub(r"<[^>]+>", "", html).strip()


async def crawl_google_news(query: str, max_results: int = 15) -> list[dict]:
    """Google News RSS 크롤링"""
    cached = _get_cached(query)
    if cached is not None:
        logger.info(f"News cache hit: {query}")
        return cached

    encoded_q = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl=ko&gl=KR&ceid=KR:ko"

    articles = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)",
            })
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "lxml-xml")
            items = soup.find_all("item")

            for item in items[:max_results]:
                title = _clean_html(item.find("title").text) if item.find("title") else ""
                link = item.find("link").text if item.find("link") else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") else ""
                source = item.find("source").text if item.find("source") else ""
                desc = _clean_html(item.find("description").text) if item.find("description") else ""

                if title:
                    articles.append({
                        "title": title,
                        "link": link,
                        "pub_date": pub_date,
                        "source": source,
                        "description": desc[:200],
                    })

        logger.info(f"Crawled {len(articles)} articles for: {query}")
        _set_cached(query, articles)

    except Exception as e:
        logger.error(f"News crawling error for '{query}': {e}")

    return articles


def build_search_queries(area_name: str, business_type: str = "") -> list[str]:
    """상권/지역에 대한 검색 쿼리 생성"""
    # 지역명에서 핵심 키워드 추출
    clean_name = area_name.replace("상권", "").strip()

    queries = [
        f"{clean_name} 상권",
        f"{clean_name} 창업",
    ]

    if business_type:
        queries.append(f"{clean_name} {business_type}")

    return queries
