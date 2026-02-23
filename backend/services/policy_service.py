"""소상공인 정부 지원정책 정보 서비스"""

import time
import hashlib
import logging
import httpx
from typing import Any

logger = logging.getLogger(__name__)

# ── 캐시 ──────────────────────────────────────────────────

_policy_cache: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 3600  # 1시간


def _cache_key(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _get_cached(key: str) -> Any | None:
    if key in _policy_cache:
        exp, data = _policy_cache[key]
        if time.time() < exp:
            return data
        del _policy_cache[key]
    return None


def _set_cached(key: str, data: Any):
    _policy_cache[key] = (time.time() + _CACHE_TTL, data)


# ── 업종 → 정책 카테고리 매핑 ─────────────────────────────

_BIZ_TO_CATEGORY: dict[str, str] = {
    "CS100001": "음식점", "CS100002": "음식점", "CS100003": "음식점",
    "CS100004": "음식점", "CS100005": "음식점", "CS100006": "음식점",
    "CS100007": "음식점", "CS100008": "음식점", "CS100009": "음식점",
    "CS100010": "음식점",
    "CS200001": "소매업", "CS200002": "서비스업",
    "CS200003": "소매업", "CS200004": "소매업", "CS200005": "소매업",
}


# ── Bizinfo API 연동 ──────────────────────────────────────

async def fetch_bizinfo_policies(
    api_key: str,
    keyword: str = "소상공인",
) -> list[dict]:
    """기업마당 API에서 지원사업 정보 조회"""
    ck = _cache_key(f"bizinfo:{keyword}")
    cached = _get_cached(ck)
    if cached is not None:
        return cached

    url = "https://www.bizinfo.go.kr/uss/rss/bizinfoApi.do"
    params = {"crtfcKey": api_key, "dataType": "json", "keyword": keyword}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("jsonArray", [])
        policies = []
        for item in items[:30]:
            policies.append({
                "title": item.get("pblancNm", ""),
                "organization": item.get("jrsdInsttNm", ""),
                "category": _classify_policy(item.get("pblancNm", "")),
                "target": item.get("trgetNm", "소상공인"),
                "period": item.get("reqstDt", "상시"),
                "url": item.get("detailUrl", item.get("pblancUrl", "")),
                "is_active": True,
            })

        _set_cached(ck, policies)
        return policies

    except Exception as e:
        logger.warning(f"Bizinfo API error: {e}")
        return []


def _classify_policy(title: str) -> str:
    """정책 제목으로 카테고리 분류"""
    if any(k in title for k in ["자금", "대출", "융자", "보증", "금리"]):
        return "자금"
    if any(k in title for k in ["교육", "훈련", "연수", "아카데미", "학교"]):
        return "교육"
    if any(k in title for k in ["컨설팅", "멘토링", "상담", "진단"]):
        return "컨설팅"
    if any(k in title for k in ["디지털", "온라인", "스마트", "배달", "플랫폼"]):
        return "디지털"
    if any(k in title for k in ["재기", "폐업", "전환", "재취업"]):
        return "재기"
    return "기타"


# ── 정적 폴백 데이터 ──────────────────────────────────────

_FALLBACK_POLICIES: list[dict] = [
    {
        "title": "소상공인 정책자금 (직접대출)",
        "organization": "소상공인시장진흥공단",
        "category": "자금",
        "target": "소상공인",
        "period": "상시 (예산 소진 시 마감)",
        "url": "https://www.semas.or.kr/web/SUP/SBI/SBIBsnFnd.kmdc",
        "is_active": True,
    },
    {
        "title": "소상공인 경영안정자금",
        "organization": "소상공인시장진흥공단",
        "category": "자금",
        "target": "경영 어려움을 겪는 소상공인",
        "period": "상시",
        "url": "https://www.semas.or.kr/web/SUP/SBI/SBIBsnFnd.kmdc",
        "is_active": True,
    },
    {
        "title": "소상공인 역량강화 교육",
        "organization": "소상공인시장진흥공단",
        "category": "교육",
        "target": "소상공인 및 예비창업자",
        "period": "연중 수시",
        "url": "https://edu.sbiz.or.kr",
        "is_active": True,
    },
    {
        "title": "소상공인 경영개선 컨설팅",
        "organization": "소상공인시장진흥공단",
        "category": "컨설팅",
        "target": "업력 1년 이상 소상공인",
        "period": "상시",
        "url": "https://www.semas.or.kr/web/SUP/SBI/SBIConsl.kmdc",
        "is_active": True,
    },
    {
        "title": "스마트 상점 기술보급 사업",
        "organization": "중소벤처기업부",
        "category": "디지털",
        "target": "소상공인 점포",
        "period": "연초 공고",
        "url": "https://www.mss.go.kr",
        "is_active": True,
    },
    {
        "title": "소상공인 디지털전환 지원",
        "organization": "소상공인시장진흥공단",
        "category": "디지털",
        "target": "디지털 역량이 부족한 소상공인",
        "period": "상시",
        "url": "https://www.sbiz.or.kr",
        "is_active": True,
    },
    {
        "title": "배달특급 입점 지원",
        "organization": "경기도/각 지자체",
        "category": "디지털",
        "target": "음식점, 소매업 소상공인",
        "period": "상시",
        "url": "https://www.specialdelivery.co.kr",
        "is_active": True,
    },
    {
        "title": "청년 창업사관학교",
        "organization": "중소벤처기업부",
        "category": "교육",
        "target": "만 39세 이하 예비/초기 창업자",
        "period": "연초 모집",
        "url": "https://start.kosmes.or.kr",
        "is_active": True,
    },
    {
        "title": "폐업 소상공인 재기 지원",
        "organization": "소상공인시장진흥공단",
        "category": "재기",
        "target": "폐업 경험 소상공인",
        "period": "상시",
        "url": "https://www.semas.or.kr",
        "is_active": True,
    },
    {
        "title": "전통시장 및 상점가 활성화",
        "organization": "소상공인시장진흥공단",
        "category": "기타",
        "target": "전통시장, 상점가 소상공인",
        "period": "연중",
        "url": "https://www.semas.or.kr/web/SUP/SMK/SMKTraMkt.kmdc",
        "is_active": True,
    },
    {
        "title": "소공인 특화지원 사업",
        "organization": "중소벤처기업부",
        "category": "자금",
        "target": "제조업 소공인 (10인 미만)",
        "period": "상시",
        "url": "https://www.mss.go.kr",
        "is_active": True,
    },
    {
        "title": "소상공인 채무조정 프로그램",
        "organization": "신용회복위원회",
        "category": "자금",
        "target": "채무 과중 소상공인",
        "period": "상시",
        "url": "https://www.ccrs.or.kr",
        "is_active": True,
    },
]


def get_fallback_policies() -> list[dict]:
    """API 키 없을 때 내장 정적 데이터 반환"""
    return _FALLBACK_POLICIES


def match_policies_to_business(
    policies: list[dict],
    business_type: str = "",
) -> list[dict]:
    """업종 기반 정책 정렬 (관련도 높은 순)"""
    biz_cat = _BIZ_TO_CATEGORY.get(business_type, "")

    def relevance(p: dict) -> int:
        score = 0
        title = p.get("title", "")
        target = p.get("target", "")
        if biz_cat == "음식점" and any(k in title + target for k in ["음식", "요식", "외식", "배달"]):
            score += 10
        if biz_cat == "소매업" and any(k in title + target for k in ["소매", "유통", "상점"]):
            score += 10
        if biz_cat == "서비스업" and any(k in title + target for k in ["서비스", "미용"]):
            score += 10
        if p.get("is_active"):
            score += 5
        if p.get("category") == "자금":
            score += 3
        return score

    return sorted(policies, key=relevance, reverse=True)
