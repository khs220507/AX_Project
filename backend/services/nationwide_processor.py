import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# 17개 시도 정보
SIDO_LIST = [
    {"code": "11", "name": "서울특별시", "short": "서울", "is_seoul": True,
     "center": [37.5665, 126.978], "zoom": 12},
    {"code": "26", "name": "부산광역시", "short": "부산", "is_seoul": False,
     "center": [35.1796, 129.0756], "zoom": 12},
    {"code": "27", "name": "대구광역시", "short": "대구", "is_seoul": False,
     "center": [35.8714, 128.6014], "zoom": 12},
    {"code": "28", "name": "인천광역시", "short": "인천", "is_seoul": False,
     "center": [37.4563, 126.7052], "zoom": 11},
    {"code": "29", "name": "광주광역시", "short": "광주", "is_seoul": False,
     "center": [35.1595, 126.8526], "zoom": 12},
    {"code": "30", "name": "대전광역시", "short": "대전", "is_seoul": False,
     "center": [36.3504, 127.3845], "zoom": 12},
    {"code": "31", "name": "울산광역시", "short": "울산", "is_seoul": False,
     "center": [35.5384, 129.3114], "zoom": 11},
    {"code": "36", "name": "세종특별자치시", "short": "세종", "is_seoul": False,
     "center": [36.4800, 127.2590], "zoom": 12},
    {"code": "41", "name": "경기도", "short": "경기", "is_seoul": False,
     "center": [37.4138, 127.5183], "zoom": 9},
    {"code": "42", "name": "강원특별자치도", "short": "강원", "is_seoul": False,
     "center": [37.8228, 128.1555], "zoom": 9},
    {"code": "43", "name": "충청북도", "short": "충북", "is_seoul": False,
     "center": [36.6357, 127.4912], "zoom": 9},
    {"code": "44", "name": "충청남도", "short": "충남", "is_seoul": False,
     "center": [36.5184, 126.8000], "zoom": 9},
    {"code": "45", "name": "전북특별자치도", "short": "전북", "is_seoul": False,
     "center": [35.7175, 127.1530], "zoom": 9},
    {"code": "46", "name": "전라남도", "short": "전남", "is_seoul": False,
     "center": [34.8679, 126.9910], "zoom": 9},
    {"code": "47", "name": "경상북도", "short": "경북", "is_seoul": False,
     "center": [36.4919, 128.8889], "zoom": 9},
    {"code": "48", "name": "경상남도", "short": "경남", "is_seoul": False,
     "center": [35.4606, 128.2132], "zoom": 9},
    {"code": "50", "name": "제주특별자치도", "short": "제주", "is_seoul": False,
     "center": [33.4996, 126.5312], "zoom": 10},
]

SIDO_MAP = {s["code"]: s for s in SIDO_LIST}

# SEMAS 대분류 코드 → 업종명 매핑
SEMAS_LARGE_CATEGORIES = {
    "Q": "음식",
    "D": "소매",
    "R": "생활서비스",
    "L": "관광/여가/오락",
    "P": "부동산",
    "F": "교육",
    "S": "스포츠",
    "O": "수리/개인",
    "N": "숙박",
}

# SEMAS 중분류 → 우리 업종 코드 매핑 (근사치)
SEMAS_MID_TO_BIZ = {
    "Q01": "CS100001",  # 한식 → 한식음식점
    "Q02": "CS100002",  # 중식 → 중식음식점
    "Q03": "CS100003",  # 일식 → 일식음식점
    "Q04": "CS100004",  # 양식 → 양식음식점
    "Q05": "CS100005",  # 제과제빵 → 제과점
    "Q06": "CS100006",  # 패스트푸드 → 패스트푸드점
    "Q07": "CS100007",  # 치킨 → 치킨전문점
    "Q08": "CS100008",  # 분식 → 분식전문점
    "Q09": "CS100009",  # 호프/주점 → 호프-간이주점
    "Q12": "CS100010",  # 커피/음료 → 커피-음료
}

# 우리 업종 목록 (프론트에서 사용하는 것과 동일)
BUSINESS_TYPES = [
    {"code": "CS100001", "name": "한식음식점"},
    {"code": "CS100002", "name": "중식음식점"},
    {"code": "CS100003", "name": "일식음식점"},
    {"code": "CS100004", "name": "양식음식점"},
    {"code": "CS100005", "name": "제과점"},
    {"code": "CS100006", "name": "패스트푸드점"},
    {"code": "CS100007", "name": "치킨전문점"},
    {"code": "CS100008", "name": "분식전문점"},
    {"code": "CS100009", "name": "호프-간이주점"},
    {"code": "CS100010", "name": "커피-음료"},
    {"code": "CS200001", "name": "일반의류"},
    {"code": "CS200002", "name": "미용실"},
    {"code": "CS200003", "name": "편의점"},
    {"code": "CS200004", "name": "슈퍼마켓"},
    {"code": "CS200005", "name": "의약품"},
]

BIZ_NAME_MAP = {b["code"]: b["name"] for b in BUSINESS_TYPES}


def _get_semas_mid_code(store: dict) -> str | None:
    """SEMAS 점포에서 중분류 코드 추출"""
    return store.get("indsMclsCd") or None


def _map_to_our_biz(store: dict) -> str | None:
    """SEMAS 점포를 우리 업종 코드로 매핑"""
    mid = _get_semas_mid_code(store)
    if mid:
        return SEMAS_MID_TO_BIZ.get(mid)
    return None


def _percentile(value: float, all_values: list[float]) -> float:
    if not all_values or value <= 0:
        return 50.0
    return (sum(1 for v in all_values if v < value) / len(all_values)) * 100


def _clamp(v: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(v)))


def compute_dong_scores(
    stores_by_dong: dict[str, list[dict]],
    target_biz_code: str | None = None,
) -> dict[str, dict]:
    """
    동별 점포 데이터로부터 점수 계산.

    Returns: {adong_cd: {total_stores, target_stores, score, breakdown}}
    """
    # 1차: 동별 기본 통계 수집
    dong_stats: dict[str, dict] = {}
    for dong_cd, stores in stores_by_dong.items():
        total = len(stores)

        # 업종 분포 계산
        category_counts: dict[str, int] = defaultdict(int)
        for s in stores:
            large = s.get("indsLclsCd", "")
            cat_name = SEMAS_LARGE_CATEGORIES.get(large, s.get("indsLclsNm", "기타"))
            category_counts[cat_name] += 1

        # 타겟 업종 점포수
        target_count = 0
        if target_biz_code:
            for s in stores:
                mapped = _map_to_our_biz(s)
                if mapped == target_biz_code:
                    target_count += 1

        # 고유 업종(중분류) 수
        unique_mid = len(set(s.get("indsMclsCd", "") for s in stores if s.get("indsMclsCd")))

        dong_stats[dong_cd] = {
            "total_stores": total,
            "target_stores": target_count,
            "unique_categories": unique_mid,
            "category_counts": dict(category_counts),
        }

    # 2차: 시도 내 백분위 계산
    all_totals = [d["total_stores"] for d in dong_stats.values() if d["total_stores"] > 0]
    all_unique = [d["unique_categories"] for d in dong_stats.values() if d["unique_categories"] > 0]
    all_target = [d["target_stores"] for d in dong_stats.values() if d["target_stores"] > 0]

    result: dict[str, dict] = {}
    for dong_cd, stats in dong_stats.items():
        # 업종 다양성 (25%): 고유 중분류 수 백분위
        diversity_score = _percentile(stats["unique_categories"], all_unique)

        # 경쟁 밀도 (30%): 타겟 업종 점포수 기반 (적을수록 좋음)
        if target_biz_code and all_target:
            competition_score = 100 - _percentile(stats["target_stores"], all_target)
        else:
            competition_score = 50  # 타겟 없으면 중립

        # 상권 활성도 (25%): 총 점포수 백분위
        activity_score = _percentile(stats["total_stores"], all_totals)

        # 업종 집중도 (20%): 분포가 고르면 높은 점수
        cats = stats["category_counts"]
        if len(cats) > 1 and stats["total_stores"] > 0:
            max_share = max(cats.values()) / stats["total_stores"]
            balance_score = _clamp((1 - max_share) * 150)  # 집중도 낮을수록 높음
        else:
            balance_score = 30

        weights = [0.25, 0.30, 0.25, 0.20]
        scores = [diversity_score, competition_score, activity_score, balance_score]
        total_score = _clamp(sum(s * w for s, w in zip(scores, weights)))

        result[dong_cd] = {
            "total_stores": stats["total_stores"],
            "target_stores": stats["target_stores"],
            "score": total_score,
            "breakdown": [
                {"category": "업종 다양성", "score": _clamp(diversity_score), "rank_pct": round(diversity_score, 1)},
                {"category": "경쟁 밀도", "score": _clamp(competition_score), "rank_pct": round(competition_score, 1)},
                {"category": "상권 활성도", "score": _clamp(activity_score), "rank_pct": round(activity_score, 1)},
                {"category": "업종 집중도", "score": _clamp(balance_score), "rank_pct": round(balance_score, 1)},
            ],
            "category_counts": stats["category_counts"],
        }

    return result


def generate_grade(score: int) -> str:
    if score >= 80:
        return "우수"
    if score >= 60:
        return "양호"
    if score >= 40:
        return "보통"
    return "주의"


def generate_recommendation_nationwide(
    dong_name: str,
    breakdown: list[dict],
    grade: str,
    total_stores: int,
) -> str:
    strengths = [b for b in breakdown if b["score"] >= 70]
    weaknesses = [b for b in breakdown if b["score"] < 40]
    parts = [f"{dong_name}"]

    if strengths:
        parts.append(f"은(는) {', '.join(b['category'] for b in strengths[:3])} 측면에서 양호한 상권입니다.")
    else:
        parts.append("은(는) 전반적으로 보통 수준의 상권입니다.")

    if weaknesses:
        parts.append(f" {', '.join(b['category'] for b in weaknesses[:2])} 부분은 유의가 필요합니다.")

    parts.append(f" (총 {total_stores}개 점포)")
    return "".join(parts)


def compute_store_analysis(
    stores: list[dict],
    dong_name: str,
    region_name: str,
    target_biz_code: str | None = None,
) -> dict:
    """동 상세 분석 (단일 동)"""
    # 카테고리 분포
    category_counts: dict[str, int] = defaultdict(int)
    for s in stores:
        large = s.get("indsLclsCd", "")
        cat_name = SEMAS_LARGE_CATEGORIES.get(large, s.get("indsLclsNm", "기타"))
        category_counts[cat_name] += 1

    total = len(stores)
    cat_distribution = sorted(
        [
            {"category": cat, "count": cnt, "percentage": round(cnt / total * 100, 1) if total else 0}
            for cat, cnt in category_counts.items()
        ],
        key=lambda x: x["count"],
        reverse=True,
    )

    # 대표 업체명
    top_businesses = []
    seen = set()
    for s in stores:
        name = s.get("bizesNm", "")
        if name and name not in seen:
            seen.add(name)
            top_businesses.append(name)
            if len(top_businesses) >= 5:
                break

    # 점수 계산
    scores = compute_dong_scores({dong_name: stores}, target_biz_code)
    dong_data = scores.get(dong_name, {
        "score": 50,
        "total_stores": total,
        "target_stores": 0,
        "breakdown": [
            {"category": "업종 다양성", "score": 50, "rank_pct": 50.0},
            {"category": "경쟁 밀도", "score": 50, "rank_pct": 50.0},
            {"category": "상권 활성도", "score": 50, "rank_pct": 50.0},
            {"category": "업종 집중도", "score": 50, "rank_pct": 50.0},
        ],
    })

    grade = generate_grade(dong_data["score"])
    recommendation = generate_recommendation_nationwide(
        dong_name, dong_data["breakdown"], grade, total
    )

    return {
        "dong_name": dong_name,
        "region_name": region_name,
        "data_source": "SEMAS",
        "total_score": dong_data["score"],
        "grade": grade,
        "breakdown": dong_data["breakdown"],
        "recommendation": recommendation,
        "store_summary": {
            "total_stores": total,
            "category_distribution": cat_distribution,
            "top_businesses": top_businesses,
        },
    }


def recommend_missing_businesses_nationwide(
    stores: list[dict],
) -> list[dict]:
    """동 내 점포 데이터 기반 미진출 업종 추천"""
    # 현재 동에 존재하는 업종 찾기 (SEMAS 중분류 → 우리 업종 코드)
    existing_biz = set()
    for s in stores:
        mapped = _map_to_our_biz(s)
        if mapped:
            existing_biz.add(mapped)

    # 매핑 가능한 업종 중 없는 것 찾기
    mappable_biz = set(SEMAS_MID_TO_BIZ.values())
    missing_biz = mappable_biz - existing_biz

    if not missing_biz:
        return []

    total_stores = len(stores)
    results = []
    for biz_code in missing_biz:
        biz_name = BIZ_NAME_MAP.get(biz_code, biz_code)

        # 경쟁도 점수: 이 동에 해당 업종이 없으므로 높은 점수
        competition_score = 85

        # 상권 규모 보정: 점포가 많은 동일수록 수요가 있을 가능성
        size_bonus = min(total_stores / 100, 1.0) * 30 if total_stores > 0 else 0

        rec_score = _clamp(competition_score * 0.6 + size_bonus + 20)

        reasons = ["경쟁 업체 부재"]
        if total_stores >= 50:
            reasons.append("활발한 상권")
        if total_stores >= 100:
            reasons.append("대규모 상권 내 블루오션")

        results.append({
            "business_code": biz_code,
            "business_name": biz_name,
            "score": rec_score,
            "avg_sales_citywide": 0,  # 전국 매출 데이터 없음
            "reason": ", ".join(reasons),
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]
