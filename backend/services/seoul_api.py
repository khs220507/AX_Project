import asyncio
import time
import hashlib
import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)

# 서울시 25개 자치구 중심 좌표 (상권영역 API 불가 시 폴백용)
DISTRICT_COORDS: dict[str, tuple[float, float]] = {
    "종로구": (37.5735, 126.9790),
    "중구": (37.5641, 126.9979),
    "용산구": (37.5326, 126.9906),
    "성동구": (37.5634, 127.0369),
    "광진구": (37.5385, 127.0823),
    "동대문구": (37.5744, 127.0396),
    "중랑구": (37.6063, 127.0928),
    "성북구": (37.5894, 127.0167),
    "강북구": (37.6396, 127.0257),
    "도봉구": (37.6688, 127.0472),
    "노원구": (37.6542, 127.0568),
    "은평구": (37.6027, 126.9291),
    "서대문구": (37.5791, 126.9368),
    "마포구": (37.5663, 126.9014),
    "양천구": (37.5170, 126.8664),
    "강서구": (37.5509, 126.8495),
    "구로구": (37.4955, 126.8878),
    "금천구": (37.4569, 126.8955),
    "영등포구": (37.5264, 126.8963),
    "동작구": (37.5124, 126.9393),
    "관악구": (37.4781, 126.9515),
    "서초구": (37.4837, 127.0324),
    "강남구": (37.5172, 127.0473),
    "송파구": (37.5146, 127.1050),
    "강동구": (37.5301, 127.1238),
}


def _area_coord_offset(area_code: str) -> tuple[float, float]:
    """상권코드 기반 좌표 오프셋 (같은 구 내 상권들이 겹치지 않게)"""
    h = int(hashlib.md5(area_code.encode()).hexdigest()[:8], 16)
    lat_offset = ((h % 1000) - 500) / 500 * 0.015  # ±0.015도
    lng_offset = (((h >> 10) % 1000) - 500) / 500 * 0.015
    return lat_offset, lng_offset


class SeoulAPIClient:
    """서울 열린데이터광장 API 클라이언트 (비동기 + 캐싱)"""

    BASE_URL = "http://openapi.seoul.go.kr:8088"

    SERVICE_SALES = "VwsmTrdarSelngQq"
    SERVICE_FLOAT_POP = "VwsmTrdarFlpopQq"
    SERVICE_STORE = "VwsmTrdarStorQq"
    SERVICE_CHANGE_IDX = "VwsmTrdarIxQq"          # 상권변화지표
    SERVICE_FACILITIES = "VwsmTrdarFcltyQq"       # 집객시설
    SERVICE_WORKER_POP = "VwsmTrdarWrcPopltnQq"  # 직장인구
    SERVICE_RESIDENT_POP = "VwsmTrdarRepopQq"    # 상주인구

    def __init__(self, api_key: str, cache_ttl: int = 3600):
        self.api_key = api_key
        self.cache_ttl = cache_ttl
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
        self._cache: dict[str, tuple[float, Any]] = {}
        self._area_map: dict[str, dict] = {}  # code → area info
        self._locks: dict[str, asyncio.Lock] = {}  # 중복 호출 방지

    def _get_cache(self, key: str) -> Any | None:
        if key in self._cache:
            expire_time, data = self._cache[key]
            if time.time() < expire_time:
                return data
            del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Any):
        self._cache[key] = (time.time() + self.cache_ttl, data)

    async def _fetch_page(self, service: str, start: int, end: int, params: str = "") -> dict:
        """서울시 API 단일 페이지 호출"""
        url_parts = [self.BASE_URL, self.api_key, "json", service, str(start), str(end)]
        if params:
            url_parts.append(params)
        url = "/".join(url_parts)

        logger.info(f"Seoul API call: {service} [{start}-{end}] {params}")
        resp = await self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    async def fetch(self, service: str, start: int = 1, end: int = 1000, params: str = "") -> list[dict]:
        """서울시 API 호출 + 캐싱"""
        cache_key = f"{service}:{start}:{end}:{params}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        try:
            data = await self._fetch_page(service, start, end, params)

            if "RESULT" in data:
                result = data["RESULT"]
                if result.get("CODE") != "INFO-000":
                    logger.warning(f"Seoul API error: {result}")
                    return []

            rows = data.get(service, {}).get("row", [])
            self._set_cache(cache_key, rows)
            return rows
        except Exception as e:
            logger.error(f"Seoul API fetch error: {e}")
            return []

    def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def fetch_all(self, service: str, params: str = "", max_pages: int = 50) -> list[dict]:
        """전체 데이터 페이징 조회 (병렬 + 중복 호출 방지)"""
        cache_key = f"all:{service}:{params}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        lock = self._get_lock(cache_key)
        async with lock:
            # 락 획득 후 다시 캐시 확인 (다른 코루틴이 이미 로드했을 수 있음)
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached

            try:
                first_data = await self._fetch_page(service, 1, 1, params)

                if "RESULT" in first_data:
                    result = first_data["RESULT"]
                    if result.get("CODE") != "INFO-000":
                        logger.warning(f"Seoul API error: {result}")
                        return []

                service_data = first_data.get(service, {})
                total = service_data.get("list_total_count", 0)

                if total == 0:
                    return []

                # 전체 페이지를 병렬로 가져오기
                page_size = 1000
                num_pages = min(max_pages, (total - 1) // page_size + 1)

                async def _fetch_one_page(page: int) -> list[dict]:
                    start = page * page_size + 1
                    end = min((page + 1) * page_size, total)
                    return await self.fetch(service, start, end, params)

                page_results = await asyncio.gather(
                    *[_fetch_one_page(p) for p in range(num_pages)]
                )

                all_rows = [row for rows in page_results for row in rows]
                self._set_cache(cache_key, all_rows)
                return all_rows

            except Exception as e:
                logger.error(f"Seoul API fetch_all error: {e}")
                return []

    # ── 상권 목록 (유동인구 데이터에서 추출) ──

    async def build_area_map(self):
        """유동인구 데이터에서 고유 상권 목록 구축"""
        if self._area_map:
            return

        # 최근 분기 유동인구 데이터에서 상권 정보 추출
        # 20252 = 2025년 2분기
        for yyqu in ["20253", "20252", "20251", "20244"]:
            rows = await self.fetch_all(self.SERVICE_FLOAT_POP, yyqu)
            if rows:
                for row in rows:
                    code = str(row.get("TRDAR_CD", ""))
                    if code and code not in self._area_map:
                        name = str(row.get("TRDAR_CD_NM", ""))
                        area_type_code = str(row.get("TRDAR_SE_CD", "A"))
                        area_type_name = str(row.get("TRDAR_SE_CD_NM", ""))

                        self._area_map[code] = {
                            "code": code,
                            "name": name,
                            "area_type_code": area_type_code,
                            "area_type_name": area_type_name,
                            "floating_pop": int(float(row.get("TOT_FLPOP_CO", 0) or 0)),
                        }
                logger.info(f"Built area map from quarter {yyqu}: {len(self._area_map)} areas")
                break

    async def get_areas(self) -> list[dict]:
        """상권 목록 반환 (좌표 포함)"""
        await self.build_area_map()
        return list(self._area_map.values())

    def get_area_info(self, code: str) -> dict | None:
        """캐시된 상권 정보 조회"""
        return self._area_map.get(code)

    # ── 분기 필터 지원 데이터 조회 ──

    async def get_sales(self, yyqu: str = "") -> list[dict]:
        """추정매출 (년분기코드 예: '20253')"""
        return await self.fetch_all(self.SERVICE_SALES, yyqu)

    async def get_sales_multi_quarters(self, yyqu_list: list[str]) -> list[dict]:
        """여러 분기 매출 데이터"""
        all_rows = []
        for yyqu in yyqu_list:
            rows = await self.get_sales(yyqu)
            all_rows.extend(rows)
        return all_rows

    async def get_floating_pop(self, yyqu: str = "") -> list[dict]:
        """추정유동인구"""
        return await self.fetch_all(self.SERVICE_FLOAT_POP, yyqu)

    async def get_stores(self, yyqu: str = "") -> list[dict]:
        """점포수"""
        return await self.fetch_all(self.SERVICE_STORE, yyqu)

    async def get_change_index(self, yyqu: str = "") -> list[dict]:
        """상권변화지표"""
        return await self.fetch_all(self.SERVICE_CHANGE_IDX, yyqu)

    async def get_facilities(self, yyqu: str = "") -> list[dict]:
        """집객시설 (학교/병원/지하철 등)"""
        return await self.fetch_all(self.SERVICE_FACILITIES, yyqu)

    async def get_worker_pop(self, yyqu: str = "") -> list[dict]:
        """직장인구"""
        return await self.fetch_all(self.SERVICE_WORKER_POP, yyqu)

    async def get_resident_pop(self, yyqu: str = "") -> list[dict]:
        """상주인구"""
        return await self.fetch_all(self.SERVICE_RESIDENT_POP, yyqu)

    async def close(self):
        await self.client.aclose()
