import logging
from typing import Any
from services.seoul_api import DISTRICT_COORDS, _area_coord_offset

logger = logging.getLogger(__name__)

# 상권유형 코드 → 한글
AREA_TYPE_MAP = {
    "A": "골목상권",
    "D": "발달상권",
    "R": "전통시장",
    "U": "관광특구",
}

# 업종 목록
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

# 최근 8분기 코드
RECENT_QUARTERS = ["20234", "20241", "20242", "20243", "20244", "20251", "20252", "20253"]


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "" or value == "null":
            return default
        return int(float(str(value)))
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "" or value == "null":
            return default
        return float(str(value))
    except (ValueError, TypeError):
        return default


def get_biz_name(code: str) -> str:
    return next((b["name"] for b in BUSINESS_TYPES if b["code"] == code), code)


def guess_district(area_name: str) -> str:
    """상권명에서 자치구 추정"""
    for gu in DISTRICT_COORDS:
        if gu.replace("구", "") in area_name:
            return gu

    name_to_gu = {
        "강남": "강남구", "역삼": "강남구", "삼성": "강남구", "선릉": "강남구",
        "신사": "강남구", "압구정": "강남구", "청담": "강남구", "논현": "강남구",
        "홍대": "마포구", "합정": "마포구", "연남": "마포구", "상수": "마포구", "망원": "마포구",
        "명동": "중구", "을지로": "중구", "충무로": "중구", "남대문": "중구",
        "이태원": "용산구", "한남": "용산구", "경리단": "용산구", "해방촌": "용산구",
        "건대": "광진구", "구의": "광진구", "자양": "광진구",
        "잠실": "송파구", "송리단": "송파구", "방이": "송파구", "석촌": "송파구",
        "성수": "성동구", "왕십리": "성동구", "뚝섬": "성동구",
        "여의도": "영등포구", "영등포": "영등포구", "당산": "영등포구",
        "신촌": "서대문구", "이대": "서대문구",
        "종로": "종로구", "광화문": "종로구", "인사동": "종로구", "북촌": "종로구",
        "혜화": "종로구", "대학로": "종로구",
        "서초": "서초구", "교대": "서초구", "방배": "서초구", "반포": "서초구",
        "동대문": "동대문구", "장안": "동대문구", "회기": "동대문구",
        "사당": "동작구", "노량진": "동작구",
        "신림": "관악구", "서울대": "관악구", "낙성대": "관악구",
        "노원": "노원구", "중계": "노원구", "상계": "노원구",
        "구로": "구로구", "가산": "금천구", "독산": "금천구",
        "목동": "양천구", "천호": "강동구", "길동": "강동구",
        "수유": "강북구", "미아": "강북구",
        "도봉": "도봉구", "창동": "도봉구",
        "불광": "은평구", "연신내": "은평구",
        "면목": "중랑구", "상봉": "중랑구",
        "정릉": "성북구", "길음": "성북구",
        "발산": "강서구", "화곡": "강서구", "마곡": "강서구",
    }

    for keyword, gu in name_to_gu.items():
        if keyword in area_name:
            return gu

    return "중구"


def area_to_summary(area_info: dict, score: int = 50) -> dict:
    """상권 정보 → API 응답용 요약"""
    code = area_info["code"]
    name = area_info["name"]
    area_type_code = area_info.get("area_type_code", "A")
    area_type = AREA_TYPE_MAP.get(area_type_code, "골목상권")
    district = guess_district(name)

    base_lat, base_lng = DISTRICT_COORDS.get(district, (37.5665, 126.978))
    lat_off, lng_off = _area_coord_offset(code)

    return {
        "code": code,
        "name": name,
        "district": district,
        "dong": "",
        "area_type": area_type,
        "lat": round(base_lat + lat_off, 6),
        "lng": round(base_lng + lng_off, 6),
        "score": score,
    }


def compute_location_score(
    area_code: str,
    sales_data: list[dict],
    pop_data: list[dict],
    store_data: list[dict],
    facility_data: list[dict] | None = None,
    change_idx_data: list[dict] | None = None,
    model_manager=None,
) -> dict:
    """입지점수 산출 (0~100) + 항목별 breakdown. ML 앙상블 우선, fallback: 룰 기반"""

    area_sales = [r for r in sales_data if str(r.get("TRDAR_CD")) == area_code]
    area_pop = [r for r in pop_data if str(r.get("TRDAR_CD")) == area_code]
    area_stores = [r for r in store_data if str(r.get("TRDAR_CD")) == area_code]

    # 1. 유동인구
    avg_pop = _avg_field(area_pop, "TOT_FLPOP_CO")
    all_pops = [safe_int(r.get("TOT_FLPOP_CO")) for r in pop_data if safe_int(r.get("TOT_FLPOP_CO")) > 0]
    pop_score = _percentile(avg_pop, all_pops)

    # 2. 매출규모
    avg_sales = _avg_field(area_sales, "THSMON_SELNG_AMT")
    all_sales_v = [safe_int(r.get("THSMON_SELNG_AMT")) for r in sales_data if safe_int(r.get("THSMON_SELNG_AMT")) > 0]
    sales_score = _percentile(avg_sales, all_sales_v)

    # 3. 경쟁강도 (낮을수록 좋음)
    avg_sim = _avg_field(area_stores, "SIMILR_INDUTY_STOR_CO")
    all_sim = [safe_int(r.get("SIMILR_INDUTY_STOR_CO")) for r in store_data if safe_int(r.get("SIMILR_INDUTY_STOR_CO")) > 0]
    competition_score = 100 - _percentile(avg_sim, all_sim)

    # 4. 성장성
    opens = sum(safe_int(r.get("OPBIZ_STOR_CO")) for r in area_stores)
    closes = sum(safe_int(r.get("CLSBIZ_STOR_CO")) for r in area_stores)
    growth_ratio = opens / max(closes, 1)
    all_growth = []
    for r in store_data:
        o, c = safe_int(r.get("OPBIZ_STOR_CO")), safe_int(r.get("CLSBIZ_STOR_CO"))
        if c > 0:
            all_growth.append(o / c)
    growth_score = _percentile(growth_ratio, all_growth) if all_growth else 50

    # 5. 안정성
    total_st = _avg_field(area_stores, "STOR_CO")
    close_rate = closes / max(total_st * max(len(area_stores), 1), 1)
    stability_score = max(0, min(100, int(100 - close_rate * 500)))

    # 6. 집객력 (주중/주말 균형)
    wd = sum(safe_int(r.get("MON_FLPOP_CO")) + safe_int(r.get("TUES_FLPOP_CO")) +
             safe_int(r.get("WED_FLPOP_CO")) + safe_int(r.get("THUR_FLPOP_CO")) +
             safe_int(r.get("FRI_FLPOP_CO")) for r in area_pop)
    we = sum(safe_int(r.get("SAT_FLPOP_CO")) + safe_int(r.get("SUN_FLPOP_CO")) for r in area_pop)
    if wd + we > 0:
        attraction_score = min(int(min(wd, we * 2.5) / max(wd, we * 2.5, 1) * 100), 100)
    else:
        attraction_score = 50

    # 7. 집객시설 (교통/학교/병원 등 인프라)
    infra_score = 50  # 기본값
    if facility_data:
        area_fac = [r for r in facility_data if str(r.get("TRDAR_CD")) == area_code]
        if area_fac:
            fac = area_fac[0]
            subway = safe_float(fac.get("SUBWAY_STATN_CO"))
            bus = safe_float(fac.get("BUS_STTN_CO"))
            school = (safe_float(fac.get("ELESCH_CO")) + safe_float(fac.get("MSKUL_CO"))
                      + safe_float(fac.get("HGSCHL_CO")) + safe_float(fac.get("UNIV_CO")))
            hospital = safe_float(fac.get("GNRL_HSPTL_CO")) + safe_float(fac.get("GEHSPT_CO"))
            etc = (safe_float(fac.get("VIATR_FCLTY_CO")) + safe_float(fac.get("SUPMK_CO"))
                   + safe_float(fac.get("THEAT_CO")) + safe_float(fac.get("STAYNG_FCLTY_CO")))
            total_fac = subway * 8 + bus * 2 + school * 3 + hospital * 4 + etc * 2

            all_fac_scores = []
            for r in facility_data:
                s = (safe_float(r.get("SUBWAY_STATN_CO")) * 8
                     + safe_float(r.get("BUS_STTN_CO")) * 2
                     + (safe_float(r.get("ELESCH_CO")) + safe_float(r.get("MSKUL_CO"))
                        + safe_float(r.get("HGSCHL_CO")) + safe_float(r.get("UNIV_CO"))) * 3
                     + (safe_float(r.get("GNRL_HSPTL_CO")) + safe_float(r.get("GEHSPT_CO"))) * 4
                     + (safe_float(r.get("VIATR_FCLTY_CO")) + safe_float(r.get("SUPMK_CO"))
                        + safe_float(r.get("THEAT_CO")) + safe_float(r.get("STAYNG_FCLTY_CO"))) * 2)
                if s > 0:
                    all_fac_scores.append(s)
            infra_score = _percentile(total_fac, all_fac_scores) if all_fac_scores else 50

    # 8. 상권활력 (변화지표)
    vitality_score = 50  # 기본값
    if change_idx_data:
        area_chg = [r for r in change_idx_data if str(r.get("TRDAR_CD")) == area_code]
        if area_chg:
            idx = area_chg[0].get("TRDAR_CHNGE_IX", "")
            vitality_map = {"HH": 85, "HL": 65, "LH": 45, "LL": 25}
            vitality_score = vitality_map.get(idx, 50)

    breakdown = [
        {"category": "유동인구", "score": _clamp(pop_score)},
        {"category": "매출규모", "score": _clamp(sales_score)},
        {"category": "경쟁강도", "score": _clamp(competition_score)},
        {"category": "성장성", "score": _clamp(growth_score)},
        {"category": "안정성", "score": _clamp(stability_score)},
        {"category": "집객력", "score": _clamp(attraction_score)},
        {"category": "인프라", "score": _clamp(infra_score)},
        {"category": "상권활력", "score": _clamp(vitality_score)},
    ]

    weights = [0.20, 0.18, 0.15, 0.12, 0.08, 0.08, 0.10, 0.09]
    total_score = _clamp(sum(b["score"] * w for b, w in zip(breakdown, weights)))

    # ML 앙상블 점수 시도
    model_used = "rule_based"
    if model_manager and model_manager.is_ready("scoring_ensemble"):
        try:
            ml_score = model_manager.predict_score(
                area_code, pop_data, sales_data, store_data, facility_data,
            )
            if ml_score is not None:
                total_score = ml_score
                model_used = "ensemble"
        except Exception:
            pass

    return {"total_score": total_score, "breakdown": breakdown, "model_used": model_used}


def generate_grade(score: int) -> str:
    if score >= 80:
        return "우수"
    if score >= 60:
        return "양호"
    if score >= 40:
        return "보통"
    return "주의"


def generate_recommendation(area_name: str, breakdown: list[dict], grade: str, biz_name: str) -> str:
    strengths = [b for b in breakdown if b["score"] >= 70]
    weaknesses = [b for b in breakdown if b["score"] < 40]
    parts = [f"{area_name} 상권"]

    if strengths:
        parts.append(f"은(는) {', '.join(b['category'] for b in strengths[:3])} 측면에서 강점을 보입니다.")
    else:
        parts.append("은(는) 전반적으로 보통 수준입니다.")

    if weaknesses:
        parts.append(f" 다만 {', '.join(b['category'] for b in weaknesses[:2])} 부분은 개선이 필요합니다.")

    if biz_name:
        if grade in ("우수", "양호"):
            parts.append(f" {biz_name} 업종 진출에 적합한 상권으로 판단됩니다.")
        else:
            parts.append(f" {biz_name} 업종 진출 시 면밀한 검토가 필요합니다.")

    return "".join(parts)


def _clamp(v: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(v)))


def _avg_field(rows: list[dict], field: str) -> float:
    vals = [safe_int(r.get(field)) for r in rows if safe_int(r.get(field)) > 0]
    return sum(vals) / len(vals) if vals else 0


def _percentile(value: float, all_values: list[float]) -> float:
    if not all_values or value <= 0:
        return 50.0
    return (sum(1 for v in all_values if v < value) / len(all_values)) * 100


def classify_district_type(
    area_code: str,
    worker_pop_data: list[dict],
    resident_pop_data: list[dict],
) -> dict:
    """직장인구/상주인구 비율로 지구유형 분류"""
    worker_rows = [r for r in worker_pop_data if str(r.get("TRDAR_CD")) == area_code]
    resident_rows = [r for r in resident_pop_data if str(r.get("TRDAR_CD")) == area_code]

    worker_pop = safe_int(worker_rows[0].get("TOT_WRC_POPLTN_CO")) if worker_rows else 0
    resident_pop = safe_int(resident_rows[0].get("TOT_REPOP_CO")) if resident_rows else 0
    household = safe_int(resident_rows[0].get("TOT_HSHLD_CO")) if resident_rows else 0

    if worker_pop == 0 and resident_pop == 0:
        district_type = "데이터없음"
    else:
        ratio = worker_pop / max(resident_pop, 1)
        if ratio > 2.0:
            district_type = "업무지구"
        elif ratio < 0.5:
            district_type = "주택지구"
        else:
            district_type = "혼합지구"

    return {
        "district_type": district_type,
        "worker_pop": worker_pop,
        "resident_pop": resident_pop,
        "household": household,
        "ratio": round(worker_pop / max(resident_pop, 1), 2) if (worker_pop + resident_pop) > 0 else 0,
    }


def compute_closure_stats(
    area_code: str,
    store_data_by_quarter: dict[str, list[dict]],
) -> dict:
    """분기별 개폐업 현황 산출"""
    quarterly = []
    total_open = 0
    total_close = 0
    total_stores = 0

    for yyqu in RECENT_QUARTERS:
        rows = store_data_by_quarter.get(yyqu, [])
        area_rows = [r for r in rows if str(r.get("TRDAR_CD")) == area_code]

        q_stores = sum(safe_int(r.get("STOR_CO")) for r in area_rows)
        q_open = sum(safe_int(r.get("OPBIZ_STOR_CO")) for r in area_rows)
        q_close = sum(safe_int(r.get("CLSBIZ_STOR_CO")) for r in area_rows)

        quarterly.append({
            "quarter": yyqu,
            "total_stores": q_stores,
            "open_stores": q_open,
            "closed_stores": q_close,
            "close_rate": round(q_close / max(q_stores, 1) * 100, 1),
        })

        total_open += q_open
        total_close += q_close
        if q_stores > 0:
            total_stores = q_stores  # 최신 분기 값 사용

    open_rate = round(total_open / max(total_stores, 1) * 100, 1)
    close_rate = round(total_close / max(total_stores, 1) * 100, 1)

    return {
        "total_stores": total_stores,
        "open_stores": total_open,
        "closed_stores": total_close,
        "open_rate": open_rate,
        "close_rate": close_rate,
        "net_change": total_open - total_close,
        "quarterly": quarterly[-4:],  # 최근 4분기만
    }


def compute_batch_scores(
    area_codes: list[str],
    sales_data: list[dict],
    pop_data: list[dict],
    store_data: list[dict],
    business_type: str | None = None,
) -> dict[str, int]:
    """전체 상권에 대해 한번에 점수 계산 (효율적 배치 처리)"""
    from collections import defaultdict

    # 업종 필터링
    if business_type:
        sales_data = [r for r in sales_data if str(r.get("SVC_INDUTY_CD")) == business_type]
        store_data = [r for r in store_data if str(r.get("SVC_INDUTY_CD")) == business_type]

    # 상권코드별로 그룹핑 (O(n) 한번만)
    sales_by_area: dict[str, list] = defaultdict(list)
    pop_by_area: dict[str, list] = defaultdict(list)
    store_by_area: dict[str, list] = defaultdict(list)

    for r in sales_data:
        sales_by_area[str(r.get("TRDAR_CD"))].append(r)
    for r in pop_data:
        pop_by_area[str(r.get("TRDAR_CD"))].append(r)
    for r in store_data:
        store_by_area[str(r.get("TRDAR_CD"))].append(r)

    # 전체 통계값 미리 계산
    all_pops = [safe_int(r.get("TOT_FLPOP_CO")) for r in pop_data if safe_int(r.get("TOT_FLPOP_CO")) > 0]
    all_sales_v = [safe_int(r.get("THSMON_SELNG_AMT")) for r in sales_data if safe_int(r.get("THSMON_SELNG_AMT")) > 0]
    all_sim_v = [safe_int(r.get("SIMILR_INDUTY_STOR_CO")) for r in store_data if safe_int(r.get("SIMILR_INDUTY_STOR_CO")) > 0]

    all_growth = []
    for r in store_data:
        o, c = safe_int(r.get("OPBIZ_STOR_CO")), safe_int(r.get("CLSBIZ_STOR_CO"))
        if c > 0:
            all_growth.append(o / c)

    weights = [0.25, 0.20, 0.20, 0.15, 0.10, 0.10]
    result: dict[str, int] = {}

    for code in area_codes:
        area_pop = pop_by_area.get(code, [])
        area_sales = sales_by_area.get(code, [])
        area_stores = store_by_area.get(code, [])

        pop_score = _percentile(_avg_field(area_pop, "TOT_FLPOP_CO"), all_pops)
        sales_score = _percentile(_avg_field(area_sales, "THSMON_SELNG_AMT"), all_sales_v)
        competition_score = 100 - _percentile(_avg_field(area_stores, "SIMILR_INDUTY_STOR_CO"), all_sim_v)

        opens = sum(safe_int(r.get("OPBIZ_STOR_CO")) for r in area_stores)
        closes = sum(safe_int(r.get("CLSBIZ_STOR_CO")) for r in area_stores)
        growth_ratio = opens / max(closes, 1)
        growth_score = _percentile(growth_ratio, all_growth) if all_growth else 50

        total_st = _avg_field(area_stores, "STOR_CO")
        close_rate = closes / max(total_st * max(len(area_stores), 1), 1)
        stability_score = max(0, min(100, int(100 - close_rate * 500)))

        wd = sum(safe_int(r.get("MON_FLPOP_CO")) + safe_int(r.get("TUES_FLPOP_CO")) +
                 safe_int(r.get("WED_FLPOP_CO")) + safe_int(r.get("THUR_FLPOP_CO")) +
                 safe_int(r.get("FRI_FLPOP_CO")) for r in area_pop)
        we = sum(safe_int(r.get("SAT_FLPOP_CO")) + safe_int(r.get("SUN_FLPOP_CO")) for r in area_pop)
        if wd + we > 0:
            attraction_score = min(int(min(wd, we * 2.5) / max(wd, we * 2.5, 1) * 100), 100)
        else:
            attraction_score = 50

        scores = [pop_score, sales_score, competition_score, growth_score, stability_score, attraction_score]
        total = _clamp(sum(s * w for s, w in zip(scores, weights)))
        result[code] = total

    return result


def recommend_missing_businesses(
    area_code: str,
    sales_data: list[dict],
    store_data: list[dict],
    pop_data: list[dict],
    model_manager=None,
    facility_data: list[dict] | None = None,
) -> list[dict]:
    """해당 상권에 없는 업종 중 추천할만한 업종 분석 (ML 추천 모델 우선)"""
    # 1. 이 상권에 존재하는 업종 코드 찾기
    area_stores = [r for r in store_data if str(r.get("TRDAR_CD")) == area_code]
    existing_biz = set()
    for r in area_stores:
        biz_cd = str(r.get("SVC_INDUTY_CD", ""))
        count = safe_int(r.get("STOR_CO"))
        if biz_cd and count > 0:
            existing_biz.add(biz_cd)

    all_biz_codes = {b["code"] for b in BUSINESS_TYPES}
    missing_biz = all_biz_codes - existing_biz

    if not missing_biz:
        return []

    # 2. 유동인구 기반 상권 매력도
    area_pop = [r for r in pop_data if str(r.get("TRDAR_CD")) == area_code]
    avg_pop = _avg_field(area_pop, "TOT_FLPOP_CO")

    # 3. 없는 업종 각각에 대해 서울 전체 평균 매출 + 경쟁 낮음 점수 산출
    results = []
    for biz_code in missing_biz:
        biz_name = get_biz_name(biz_code)

        # 이 업종의 서울 전체 매출 데이터
        biz_sales = [r for r in sales_data if str(r.get("SVC_INDUTY_CD")) == biz_code]
        avg_sales = _avg_field(biz_sales, "THSMON_SELNG_AMT") if biz_sales else 0

        # 이 업종의 서울 전체 점포수
        biz_stores = [r for r in store_data if str(r.get("SVC_INDUTY_CD")) == biz_code]
        total_stores = sum(safe_int(r.get("STOR_CO")) for r in biz_stores)
        num_areas_with_biz = len(set(str(r.get("TRDAR_CD")) for r in biz_stores if safe_int(r.get("STOR_CO")) > 0))

        # 경쟁도 (해당 업종이 얼마나 많은 상권에 존재하는지)
        competition = num_areas_with_biz / max(len(set(str(r.get("TRDAR_CD")) for r in store_data)), 1)
        competition_score = max(0, 100 - int(competition * 150))  # 적을수록 높은 점수

        # 매출 잠재력 (서울 평균 매출 기반)
        all_biz_avg_sales = []
        for bt in BUSINESS_TYPES:
            bt_sales = [r for r in sales_data if str(r.get("SVC_INDUTY_CD")) == bt["code"]]
            if bt_sales:
                all_biz_avg_sales.append(_avg_field(bt_sales, "THSMON_SELNG_AMT"))
        sales_potential = _percentile(avg_sales, all_biz_avg_sales) if all_biz_avg_sales else 50

        # 종합 추천 점수: 경쟁 낮음(40%) + 매출 잠재력(35%) + 유동인구 보정(25%)
        pop_bonus = min(avg_pop / 50000, 1.0) * 100 if avg_pop > 0 else 50
        rec_score = int(competition_score * 0.4 + sales_potential * 0.35 + pop_bonus * 0.25)
        rec_score = max(0, min(100, rec_score))

        # 추천 이유 생성
        reasons = []
        if competition_score >= 70:
            reasons.append("경쟁 업체 부재")
        elif competition_score >= 40:
            reasons.append("낮은 경쟁도")
        if sales_potential >= 60:
            reasons.append("높은 매출 잠재력")
        if pop_bonus >= 70:
            reasons.append("풍부한 유동인구")
        if not reasons:
            reasons.append("블루오션 기회")

        results.append({
            "business_code": biz_code,
            "business_name": biz_name,
            "score": rec_score,
            "avg_sales_citywide": int(avg_sales),
            "reason": ", ".join(reasons),
        })

    # 점수 높은 순 정렬
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:5]  # 상위 5개만
