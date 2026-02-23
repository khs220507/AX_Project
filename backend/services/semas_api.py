import time
import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)


class SEMASAPIClient:
    """소상공인시장진흥공단 상권정보 API 클라이언트 (전국 점포 데이터)"""

    def __init__(self, base_url: str, api_key: str, cache_ttl: int = 3600):
        self.base_url = base_url
        self.api_key = api_key
        self.cache_ttl = cache_ttl
        self.client = httpx.AsyncClient(timeout=30.0)
        self._cache: dict[str, tuple[float, Any]] = {}

    def _get_cache(self, key: str) -> Any | None:
        if key in self._cache:
            expire_time, data = self._cache[key]
            if time.time() < expire_time:
                return data
            del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Any):
        self._cache[key] = (time.time() + self.cache_ttl, data)

    async def _fetch(self, endpoint: str, params: dict) -> dict:
        """SEMAS API 단일 호출"""
        params["serviceKey"] = self.api_key
        params["type"] = "json"
        params.setdefault("numOfRows", "1000")
        url = f"{self.base_url}/{endpoint}"

        logger.info(f"SEMAS API call: {endpoint} params={{{k}: {v} for k, v in params.items() if k != 'serviceKey'}}")
        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _fetch_all_pages(self, endpoint: str, params: dict, max_pages: int = 20) -> list[dict]:
        """페이징으로 전체 데이터 조회"""
        all_items = []
        for page in range(1, max_pages + 1):
            params["pageNo"] = str(page)
            try:
                data = await self._fetch(endpoint, params.copy())
                body = data.get("body", {})
                items = body.get("items", [])
                if not items:
                    break
                all_items.extend(items)
                total_count = int(body.get("totalCount", 0))
                if len(all_items) >= total_count:
                    break
            except Exception as e:
                logger.error(f"SEMAS API page {page} error: {e}")
                break
        return all_items

    async def get_stores_in_dong(
        self,
        adong_cd: str,
        inds_lclscd: str | None = None,
        inds_mclscd: str | None = None,
    ) -> list[dict]:
        """행정동별 점포 목록 조회"""
        cache_key = f"stores_dong:{adong_cd}:{inds_lclscd}:{inds_mclscd}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        params: dict[str, str] = {"divId": "adongCd", "key": adong_cd}
        if inds_lclscd:
            params["indsLclsCd"] = inds_lclscd
        if inds_mclscd:
            params["indsMclsCd"] = inds_mclscd

        items = await self._fetch_all_pages("storeListInDong", params)
        self._set_cache(cache_key, items)
        return items

    async def get_stores_in_signgu(self, signgu_cd: str) -> list[dict]:
        """시군구별 점포 목록 조회"""
        cache_key = f"stores_signgu:{signgu_cd}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        params: dict[str, str] = {"divId": "signguCd", "key": signgu_cd}
        items = await self._fetch_all_pages("storeListInDong", params, max_pages=50)
        self._set_cache(cache_key, items)
        return items

    async def get_zones_in_admin(self, admin_cd: str) -> list[dict]:
        """행정구역별 상권 정보 조회"""
        cache_key = f"zones_admin:{admin_cd}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        params: dict[str, str] = {"divId": "adongCd", "key": admin_cd}
        try:
            data = await self._fetch("storeZoneInAdmi", params)
            items = data.get("body", {}).get("items", [])
        except Exception as e:
            logger.error(f"SEMAS zones error: {e}")
            items = []

        self._set_cache(cache_key, items)
        return items

    async def get_industry_codes(self) -> dict:
        """업종 분류 코드 조회"""
        cache_key = "industry_codes"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        try:
            large_data = await self._fetch("largeUpjongList", {})
            middle_data = await self._fetch("middleUpjongList", {})
            result = {
                "large": large_data.get("body", {}).get("items", []),
                "middle": middle_data.get("body", {}).get("items", []),
            }
        except Exception as e:
            logger.error(f"SEMAS industry codes error: {e}")
            result = {"large": [], "middle": []}

        self._set_cache(cache_key, result)
        return result

    async def close(self):
        await self.client.aclose()
