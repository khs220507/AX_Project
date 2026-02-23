"""
고급 분석 모델 7종
- 고객 특성 분석, 수요예측, 배달 최적화, 메뉴 트렌드,
  생존 예측, 재무 진단, 경영전략 추천
"""

import logging
from services.data_processor import (
    safe_int, _avg_field, _percentile, _clamp,
    RECENT_QUARTERS, BUSINESS_TYPES, get_biz_name,
)

logger = logging.getLogger(__name__)


# ── 2. 수요예측모델 ──────────────────────────────────────

def compute_demand_analysis(
    area_code: str,
    pop_data: list[dict],
    sales_data: list[dict],
) -> dict:
    area_pop = [r for r in pop_data if str(r.get("TRDAR_CD")) == area_code]
    area_sales = [r for r in sales_data if str(r.get("TRDAR_CD")) == area_code]

    time_labels = ["00-06시", "06-11시", "11-14시", "14-17시", "17-21시", "21-24시"]
    pop_fields = [f"TMZON_{i}_FLPOP_CO" for i in range(1, 7)]
    sales_fields = [f"TMZON_{i}_SELNG_AMT" for i in range(1, 7)]

    hourly_pop = []
    for label, field in zip(time_labels, pop_fields):
        count = sum(safe_int(r.get(field)) for r in area_pop)
        hourly_pop.append({"time_slot": label, "population": count})

    hourly_sales = []
    for label, field in zip(time_labels, sales_fields):
        amount = sum(safe_int(r.get(field)) for r in area_sales)
        hourly_sales.append({"time_slot": label, "sales": amount})

    day_labels = ["월", "화", "수", "목", "금", "토", "일"]
    day_pop_fields = ["MON_FLPOP_CO", "TUES_FLPOP_CO", "WED_FLPOP_CO",
                      "THUR_FLPOP_CO", "FRI_FLPOP_CO", "SAT_FLPOP_CO", "SUN_FLPOP_CO"]
    day_sales_fields = ["MON_SELNG_AMT", "TUES_SELNG_AMT", "WED_SELNG_AMT",
                        "THUR_SELNG_AMT", "FRI_SELNG_AMT", "SAT_SELNG_AMT", "SUN_SELNG_AMT"]

    daily_pop = []
    for label, field in zip(day_labels, day_pop_fields):
        count = sum(safe_int(r.get(field)) for r in area_pop)
        daily_pop.append({"day": label, "population": count})

    daily_sales = []
    for label, field in zip(day_labels, day_sales_fields):
        amount = sum(safe_int(r.get(field)) for r in area_sales)
        daily_sales.append({"day": label, "sales": amount})

    total_hourly = sum(h["population"] for h in hourly_pop) or 1
    for h in hourly_pop:
        h["ratio"] = round(h["population"] / total_hourly * 100, 1)

    total_daily = sum(d["population"] for d in daily_pop) or 1
    for d in daily_pop:
        d["ratio"] = round(d["population"] / total_daily * 100, 1)

    peak_time = max(hourly_pop, key=lambda x: x["population"])["time_slot"] if hourly_pop else "11-14시"
    peak_day = max(daily_pop, key=lambda x: x["population"])["day"] if daily_pop else "금"

    weekday_pop_total = sum(d["population"] for d in daily_pop[:5])
    weekend_pop_total = sum(d["population"] for d in daily_pop[5:])
    weekend_ratio = round(weekend_pop_total / max(weekday_pop_total + weekend_pop_total, 1) * 100, 1)

    recs = []
    if "17-21" in peak_time:
        recs.append("저녁 시간대 수요가 가장 높습니다. 디너 타임 영업 강화를 추천합니다")
    elif "11-14" in peak_time:
        recs.append("점심 시간대 수요가 가장 높습니다. 런치 메뉴/세트 구성을 추천합니다")
    elif "06-11" in peak_time:
        recs.append("오전 시간대 수요가 높습니다. 모닝/브런치 메뉴를 고려하세요")

    if weekend_ratio > 45:
        recs.append("주말 수요 비중이 높아 주말 특별 프로모션이 효과적입니다")
    elif weekend_ratio < 25:
        recs.append("평일 수요 위주로 직장인 타겟 마케팅이 유효합니다")

    return {
        "hourly_population": hourly_pop,
        "hourly_sales": hourly_sales,
        "daily_population": daily_pop,
        "daily_sales": daily_sales,
        "peak_time": peak_time,
        "peak_day": peak_day,
        "weekend_ratio": weekend_ratio,
        "recommendation": ". ".join(recs) if recs else "수요 패턴 데이터가 부족합니다",
    }


# ── 3. 고객 특성 분석 ─────────────────────────────────────

def compute_customer_profile(
    area_code: str,
    pop_data: list[dict],
    sales_data: list[dict],
) -> dict:
    area_pop = [r for r in pop_data if str(r.get("TRDAR_CD")) == area_code]
    area_sales = [r for r in sales_data if str(r.get("TRDAR_CD")) == area_code]

    total_male = sum(safe_int(r.get("ML_FLPOP_CO")) for r in area_pop)
    total_female = sum(safe_int(r.get("FML_FLPOP_CO")) for r in area_pop)
    total_gender = total_male + total_female or 1

    male_ratio = round(total_male / total_gender * 100, 1)
    female_ratio = round(total_female / total_gender * 100, 1)

    age_fields = [
        ("10대", "AGRDE_10_FLPOP_CO"),
        ("20대", "AGRDE_20_FLPOP_CO"),
        ("30대", "AGRDE_30_FLPOP_CO"),
        ("40대", "AGRDE_40_FLPOP_CO"),
        ("50대", "AGRDE_50_FLPOP_CO"),
        ("60대+", "AGRDE_60_ABOVE_FLPOP_CO"),
    ]

    age_dist = []
    total_age_pop = 0
    for age_name, field in age_fields:
        count = sum(safe_int(r.get(field)) for r in area_pop)
        total_age_pop += count
        age_dist.append({"age_group": age_name, "population": count})

    for item in age_dist:
        item["ratio"] = round(item["population"] / max(total_age_pop, 1) * 100, 1)

    main_age = max(age_dist, key=lambda x: x["population"])["age_group"] if age_dist else "30대"
    main_gender = "남성" if total_male > total_female else "여성"
    main_customer = f"{main_age} {main_gender}"

    sales_age_fields = [
        ("10대", "AGRDE_10_SELNG_AMT"),
        ("20대", "AGRDE_20_SELNG_AMT"),
        ("30대", "AGRDE_30_SELNG_AMT"),
        ("40대", "AGRDE_40_SELNG_AMT"),
        ("50대", "AGRDE_50_SELNG_AMT"),
        ("60대+", "AGRDE_60_ABOVE_SELNG_AMT"),
    ]

    sales_by_age = []
    for age_name, field in sales_age_fields:
        amount = sum(safe_int(r.get(field)) for r in area_sales)
        sales_by_age.append({"age_group": age_name, "sales": amount})

    male_sales = sum(safe_int(r.get("ML_SELNG_AMT")) for r in area_sales)
    female_sales = sum(safe_int(r.get("FML_SELNG_AMT")) for r in area_sales)

    recs = []
    if main_age in ("20대", "30대"):
        recs.append("젊은 고객층이 주를 이루어 SNS 마케팅이 효과적입니다")
    elif main_age in ("40대", "50대"):
        recs.append("중장년 고객층이 많아 품질과 서비스 중심 마케팅을 추천합니다")
    elif main_age == "60대+":
        recs.append("시니어 고객 비중이 높아 접근성과 편의성을 중시하세요")

    if abs(male_ratio - female_ratio) < 10:
        recs.append("남녀 비율이 균형적이어서 유니섹스 전략이 유효합니다")
    elif male_ratio > 60:
        recs.append("남성 고객 비중이 높아 남성 타겟 마케팅을 추천합니다")
    elif female_ratio > 60:
        recs.append("여성 고객 비중이 높아 여성 타겟 마케팅을 추천합니다")

    return {
        "male_ratio": male_ratio,
        "female_ratio": female_ratio,
        "age_distribution": age_dist,
        "main_customer": main_customer,
        "sales_by_age": sales_by_age,
        "male_sales": male_sales,
        "female_sales": female_sales,
        "recommendation": ". ".join(recs) if recs else "고객 데이터가 부족합니다",
    }


# ── 4. 배달 최적화 ────────────────────────────────────────

def compute_delivery_optimization(
    area_code: str,
    pop_data: list[dict],
    sales_data: list[dict],
    store_data: list[dict],
) -> dict:
    area_pop = [r for r in pop_data if str(r.get("TRDAR_CD")) == area_code]
    area_sales = [r for r in sales_data if str(r.get("TRDAR_CD")) == area_code]
    area_stores = [r for r in store_data if str(r.get("TRDAR_CD")) == area_code]

    total_pop = sum(safe_int(r.get("TOT_FLPOP_CO")) for r in area_pop) or 1
    night_pop = sum(safe_int(r.get("TMZON_6_FLPOP_CO")) for r in area_pop)
    night_ratio = round(night_pop / total_pop * 100, 1)

    weekday_pop = sum(
        safe_int(r.get("MON_FLPOP_CO")) + safe_int(r.get("TUES_FLPOP_CO")) +
        safe_int(r.get("WED_FLPOP_CO")) + safe_int(r.get("THUR_FLPOP_CO")) +
        safe_int(r.get("FRI_FLPOP_CO"))
        for r in area_pop
    )
    weekend_pop = sum(
        safe_int(r.get("SAT_FLPOP_CO")) + safe_int(r.get("SUN_FLPOP_CO"))
        for r in area_pop
    )
    weekend_ratio = round(weekend_pop / max(weekday_pop + weekend_pop, 1) * 100, 1)

    delivery_biz_codes = {"CS100001", "CS100002", "CS100003", "CS100004",
                          "CS100006", "CS100007", "CS100008"}
    delivery_stores = sum(
        safe_int(r.get("STOR_CO"))
        for r in area_stores
        if str(r.get("SVC_INDUTY_CD")) in delivery_biz_codes
    )
    total_stores = sum(safe_int(r.get("STOR_CO")) for r in area_stores) or 1
    delivery_store_ratio = round(delivery_stores / total_stores * 100, 1)

    delivery_competition = sum(
        safe_int(r.get("SIMILR_INDUTY_STOR_CO"))
        for r in area_stores
        if str(r.get("SVC_INDUTY_CD")) in delivery_biz_codes
    )

    night_score = min(night_ratio * 5, 30)
    weekend_score = min(weekend_ratio * 0.5, 20)
    pop_density_score = min(total_pop / 100000, 1.0) * 25
    competition_factor = max(0, 25 - delivery_competition * 2)

    delivery_score = _clamp(int(night_score + weekend_score + pop_density_score + competition_factor))

    time_fields = [
        ("00-06시", "TMZON_1_FLPOP_CO"), ("06-11시", "TMZON_2_FLPOP_CO"),
        ("11-14시", "TMZON_3_FLPOP_CO"), ("14-17시", "TMZON_4_FLPOP_CO"),
        ("17-21시", "TMZON_5_FLPOP_CO"), ("21-24시", "TMZON_6_FLPOP_CO"),
    ]
    time_pops = [(label, sum(safe_int(r.get(field)) for r in area_pop))
                 for label, field in time_fields]
    sorted_times = sorted(time_pops, key=lambda x: x[1], reverse=True)
    recommended_times = [t[0] for t in sorted_times[:3]]

    # 야간 매출 비율
    night_sales = sum(safe_int(r.get("TMZON_6_SELNG_AMT")) for r in area_sales)
    total_sales = sum(safe_int(r.get("THSMON_SELNG_AMT")) for r in area_sales) or 1
    night_sales_ratio = round(night_sales / total_sales * 100, 1)

    recs = []
    if delivery_score >= 70:
        recs.append("배달 수요가 매우 높은 상권입니다. 배달 플랫폼 입점을 적극 추천합니다")
    elif delivery_score >= 50:
        recs.append("배달 수요가 적당한 상권입니다. 피크 시간대 배달을 추천합니다")
    else:
        recs.append("오프라인 방문 수요가 주를 이루는 상권입니다. 테이크아웃 위주로 검토하세요")

    if night_ratio > 15:
        recs.append("야간 수요가 높아 심야 배달 서비스가 유효합니다")

    return {
        "delivery_score": delivery_score,
        "night_demand_ratio": night_ratio,
        "night_sales_ratio": night_sales_ratio,
        "weekend_demand_ratio": weekend_ratio,
        "delivery_store_ratio": delivery_store_ratio,
        "delivery_competition": delivery_competition,
        "recommended_times": recommended_times,
        "recommendation": ". ".join(recs),
    }


# ── 5. 메뉴 트렌드 ────────────────────────────────────────

def compute_menu_trend(
    area_code: str,
    sales_data: list[dict],
    store_data: list[dict],
    all_sales_multi_q: list[dict],
) -> dict:
    area_sales = [r for r in sales_data if str(r.get("TRDAR_CD")) == area_code]
    area_stores = [r for r in store_data if str(r.get("TRDAR_CD")) == area_code]

    biz_current: dict[str, dict] = {}
    for biz in BUSINESS_TYPES:
        code = biz["code"]
        sales = sum(safe_int(r.get("THSMON_SELNG_AMT"))
                    for r in area_sales if str(r.get("SVC_INDUTY_CD")) == code)
        stores = sum(safe_int(r.get("STOR_CO"))
                     for r in area_stores if str(r.get("SVC_INDUTY_CD")) == code)
        competition = sum(safe_int(r.get("SIMILR_INDUTY_STOR_CO"))
                         for r in area_stores if str(r.get("SVC_INDUTY_CD")) == code)
        if sales > 0 or stores > 0:
            biz_current[code] = {
                "name": biz["name"],
                "sales": sales,
                "stores": stores,
                "competition": competition,
                "per_store_sales": sales // max(stores, 1),
            }

    area_multi_sales = [r for r in all_sales_multi_q if str(r.get("TRDAR_CD")) == area_code]

    growth_by_biz: dict[str, float] = {}
    for biz in BUSINESS_TYPES:
        code = biz["code"]
        biz_quarters = [r for r in area_multi_sales if str(r.get("SVC_INDUTY_CD")) == code]
        if len(biz_quarters) >= 2:
            biz_quarters.sort(key=lambda r: str(r.get("STDR_YYQU_CD", "")))
            old_sales = safe_int(biz_quarters[0].get("THSMON_SELNG_AMT"))
            new_sales = safe_int(biz_quarters[-1].get("THSMON_SELNG_AMT"))
            if old_sales > 0:
                growth_by_biz[code] = round((new_sales - old_sales) / old_sales * 100, 1)

    growing = []
    declining = []

    for code, growth in sorted(growth_by_biz.items(), key=lambda x: x[1], reverse=True):
        info = biz_current.get(code)
        if not info:
            continue
        item = {
            "business_code": code,
            "business_name": info["name"],
            "growth_rate": growth,
            "current_sales": info["sales"],
            "store_count": info["stores"],
        }
        if growth > 0:
            growing.append(item)
        else:
            declining.append(item)

    competition_map = []
    for code, info in sorted(biz_current.items(), key=lambda x: x[1]["competition"], reverse=True):
        competition_map.append({
            "business_name": info["name"],
            "store_count": info["stores"],
            "competition": info["competition"],
            "per_store_sales": info["per_store_sales"],
        })

    recs = []
    if growing:
        recs.append(f"'{growing[0]['business_name']}' 업종이 가장 빠르게 성장하고 있습니다")
    if declining:
        recs.append(f"'{declining[0]['business_name']}' 업종은 매출이 감소 추세입니다")

    high_efficiency = sorted(
        [v for v in biz_current.values() if v["per_store_sales"] > 0],
        key=lambda x: x["per_store_sales"], reverse=True
    )
    if high_efficiency:
        recs.append(f"점포당 매출이 가장 높은 업종은 '{high_efficiency[0]['name']}'입니다")

    return {
        "growing_businesses": growing[:5],
        "declining_businesses": declining[:5],
        "competition_map": competition_map[:10],
        "recommendation": ". ".join(recs) if recs else "업종 트렌드 데이터가 부족합니다",
    }


# ── 7. 생존 예측 ──────────────────────────────────────────

def compute_survival_prediction(
    area_code: str,
    store_data: list[dict],
    store_data_by_quarter: dict[str, list[dict]],
    pop_data: list[dict],
    sales_data: list[dict],
    model_manager=None,
    facility_data: list[dict] | None = None,
) -> dict:
    # PyTorch MLP 생존 예측 시도
    ml_survival = None
    if model_manager and model_manager.is_ready("survival_mlp"):
        try:
            ml_survival = model_manager.predict_survival(
                area_code, pop_data, sales_data, store_data, facility_data,
            )
        except Exception as e:
            logger.warning(f"ML survival prediction failed: {e}")

    area_stores = [r for r in store_data if str(r.get("TRDAR_CD")) == area_code]
    area_pop = [r for r in pop_data if str(r.get("TRDAR_CD")) == area_code]
    area_sales = [r for r in sales_data if str(r.get("TRDAR_CD")) == area_code]

    quarterly_close_rates = []
    for yyqu in RECENT_QUARTERS:
        rows = store_data_by_quarter.get(yyqu, [])
        area_rows = [r for r in rows if str(r.get("TRDAR_CD")) == area_code]
        q_stores = sum(safe_int(r.get("STOR_CO")) for r in area_rows)
        q_close = sum(safe_int(r.get("CLSBIZ_STOR_CO")) for r in area_rows)
        if q_stores > 0:
            quarterly_close_rates.append(q_close / q_stores)

    avg_close_rate = (sum(quarterly_close_rates) / len(quarterly_close_rates)
                      if quarterly_close_rates else 0.05)

    quarterly_survival = 1 - avg_close_rate
    survival_1yr = round(max(0, min(100, (quarterly_survival ** 4) * 100)), 1)
    survival_3yr = round(max(0, min(100, (quarterly_survival ** 12) * 100)), 1)
    survival_5yr = round(max(0, min(100, (quarterly_survival ** 20) * 100)), 1)

    risk_factors: list[dict] = []
    positive_factors: list[dict] = []

    # 경쟁 강도
    avg_comp = _avg_field(area_stores, "SIMILR_INDUTY_STOR_CO")
    all_comp = [safe_int(r.get("SIMILR_INDUTY_STOR_CO"))
                for r in store_data if safe_int(r.get("SIMILR_INDUTY_STOR_CO")) > 0]
    comp_pct = _percentile(avg_comp, all_comp)

    if comp_pct > 70:
        risk_factors.append({
            "factor": "높은 경쟁 강도",
            "impact": f"상위 {round(100-comp_pct)}% 경쟁 밀도",
            "severity": "high",
        })
    elif comp_pct < 30:
        positive_factors.append({
            "factor": "낮은 경쟁 강도",
            "impact": "동종 업종 경쟁이 적음",
            "severity": "high",
        })

    # 유동인구
    avg_pop = _avg_field(area_pop, "TOT_FLPOP_CO")
    all_pops = [safe_int(r.get("TOT_FLPOP_CO"))
                for r in pop_data if safe_int(r.get("TOT_FLPOP_CO")) > 0]
    pop_pct = _percentile(avg_pop, all_pops)

    if pop_pct > 60:
        positive_factors.append({
            "factor": "풍부한 유동인구",
            "impact": f"상위 {round(100-pop_pct)}% 유동인구",
            "severity": "high",
        })
    elif pop_pct < 30:
        risk_factors.append({
            "factor": "낮은 유동인구",
            "impact": "유동인구가 적어 고객 확보 어려움",
            "severity": "medium",
        })

    # 매출 수준
    avg_sales = _avg_field(area_sales, "THSMON_SELNG_AMT")
    all_sales = [safe_int(r.get("THSMON_SELNG_AMT"))
                 for r in sales_data if safe_int(r.get("THSMON_SELNG_AMT")) > 0]
    sales_pct = _percentile(avg_sales, all_sales)

    if sales_pct > 60:
        positive_factors.append({
            "factor": "높은 매출 수준",
            "impact": f"서울 상위 {round(100-sales_pct)}% 매출",
            "severity": "high",
        })
    elif sales_pct < 30:
        risk_factors.append({
            "factor": "낮은 매출 수준",
            "impact": "서울 평균 대비 매출 부진",
            "severity": "high",
        })

    # 성장 추세
    opens = sum(safe_int(r.get("OPBIZ_STOR_CO")) for r in area_stores)
    closes = sum(safe_int(r.get("CLSBIZ_STOR_CO")) for r in area_stores)
    if opens > closes:
        positive_factors.append({
            "factor": "성장 중인 상권",
            "impact": f"개업({opens}) > 폐업({closes})",
            "severity": "medium",
        })
    elif closes > opens * 1.5:
        risk_factors.append({
            "factor": "쇠퇴 중인 상권",
            "impact": f"폐업({closes})이 개업({opens})보다 많음",
            "severity": "high",
        })

    if survival_3yr >= 70:
        grade = "안전"
    elif survival_3yr >= 50:
        grade = "양호"
    elif survival_3yr >= 30:
        grade = "주의"
    else:
        grade = "위험"

    parts = []
    if survival_3yr >= 70:
        parts.append("3년 생존율이 높은 안정적인 상권입니다")
    elif survival_3yr >= 50:
        parts.append("보통 수준의 생존율을 보이는 상권입니다")
    else:
        parts.append("생존율이 낮아 신중한 검토가 필요합니다")
    if risk_factors:
        parts.append(f"주요 위험 요인은 '{risk_factors[0]['factor']}'입니다")
    if positive_factors:
        parts.append(f"'{positive_factors[0]['factor']}' 등 긍정 요인도 있습니다")

    result = {
        "survival_1yr": survival_1yr,
        "survival_3yr": survival_3yr,
        "survival_5yr": survival_5yr,
        "avg_quarterly_close_rate": round(avg_close_rate * 100, 2),
        "risk_factors": risk_factors,
        "positive_factors": positive_factors,
        "grade": grade,
        "recommendation": ". ".join(parts),
        "model_used": "rule_based",
    }

    # ML 결과로 생존율 덮어쓰기 (위험/긍정 요인 등은 룰 기반 유지)
    if ml_survival:
        result["survival_1yr"] = ml_survival["survival_1yr"]
        result["survival_3yr"] = ml_survival["survival_3yr"]
        result["survival_5yr"] = ml_survival["survival_5yr"]
        result["model_used"] = "MLP"
        # grade 재계산
        s3 = ml_survival["survival_3yr"]
        if s3 >= 70:
            result["grade"] = "안전"
        elif s3 >= 50:
            result["grade"] = "양호"
        elif s3 >= 30:
            result["grade"] = "주의"
        else:
            result["grade"] = "위험"

    return result


# ── 8. 재무 진단 ──────────────────────────────────────────

# 업종별 추정 원가율
_COST_RATIOS: dict[str, float] = {
    "CS100001": 0.65, "CS100002": 0.60, "CS100003": 0.60,
    "CS100004": 0.60, "CS100005": 0.55, "CS100006": 0.55,
    "CS100007": 0.60, "CS100008": 0.60, "CS100009": 0.55,
    "CS100010": 0.45, "CS200001": 0.50, "CS200002": 0.35,
    "CS200003": 0.70, "CS200004": 0.75, "CS200005": 0.65,
}

# 서울 25개 구별 월 환산임대료 (원/3.3㎡ = 1평)
# 출처: 서울신용보증재단 기준 추정 (환산임대료 = 보증금×12%/12 + 월세)
_DISTRICT_RENT: dict[str, int] = {
    "강남구": 580000, "서초구": 520000, "중구": 550000,
    "종로구": 420000, "마포구": 400000, "영등포구": 380000,
    "용산구": 430000, "성동구": 360000, "송파구": 380000,
    "강동구": 300000, "광진구": 320000, "동대문구": 280000,
    "중랑구": 220000, "성북구": 250000, "강북구": 210000,
    "도봉구": 200000, "노원구": 210000, "은평구": 230000,
    "서대문구": 280000, "양천구": 260000, "강서구": 270000,
    "구로구": 260000, "금천구": 240000, "동작구": 290000,
    "관악구": 250000,
}

# 업종별 평균 점포 면적 (평)
_BIZ_AVG_AREA: dict[str, int] = {
    "CS100001": 15, "CS100002": 18, "CS100003": 15,
    "CS100004": 18, "CS100005": 12, "CS100006": 12,
    "CS100007": 12, "CS100008": 10, "CS100009": 18,
    "CS100010": 12, "CS200001": 15, "CS200002": 10,
    "CS200003": 10, "CS200004": 25, "CS200005": 10,
}


def compute_financial_diagnosis(
    area_code: str,
    sales_data: list[dict],
    store_data: list[dict],
    all_sales_multi_q: list[dict],
    business_type: str = "CS100001",
    district: str = "",
) -> dict:
    biz_sales = [r for r in sales_data
                 if str(r.get("TRDAR_CD")) == area_code
                 and str(r.get("SVC_INDUTY_CD")) == business_type]
    biz_stores = [r for r in store_data
                  if str(r.get("TRDAR_CD")) == area_code
                  and str(r.get("SVC_INDUTY_CD")) == business_type]

    total_sales = sum(safe_int(r.get("THSMON_SELNG_AMT")) for r in biz_sales)
    total_stores = sum(safe_int(r.get("STOR_CO")) for r in biz_stores) or 1
    sales_per_store = total_sales // total_stores

    all_biz_sales = [r for r in sales_data if str(r.get("SVC_INDUTY_CD")) == business_type]
    all_biz_stores = [r for r in store_data if str(r.get("SVC_INDUTY_CD")) == business_type]
    city_total_sales = sum(safe_int(r.get("THSMON_SELNG_AMT")) for r in all_biz_sales)
    city_total_stores = sum(safe_int(r.get("STOR_CO")) for r in all_biz_stores) or 1
    city_avg_per_store = city_total_sales // city_total_stores

    vs_city_avg = round(sales_per_store / max(city_avg_per_store, 1) * 100, 1)

    # 원가 계산
    cost_ratio = _COST_RATIOS.get(business_type, 0.60)
    estimated_cost = int(sales_per_store * cost_ratio)

    # 임대료 계산
    rent_per_pyeong = _DISTRICT_RENT.get(district, 300000)
    avg_area = _BIZ_AVG_AREA.get(business_type, 15)
    estimated_rent = rent_per_pyeong * avg_area

    # 실질 이익 (매출 - 원가 - 임대료)
    estimated_profit = sales_per_store - estimated_cost - estimated_rent

    if sales_per_store > 0:
        profit_margin = round(estimated_profit / sales_per_store * 100, 1)
        rent_ratio = round(estimated_rent / sales_per_store * 100, 1)
    else:
        profit_margin = 0.0
        rent_ratio = 0.0

    if rent_ratio <= 15:
        rent_grade = "적정"
    elif rent_ratio <= 25:
        rent_grade = "주의"
    else:
        rent_grade = "과다"

    area_multi = [
        r for r in all_sales_multi_q
        if str(r.get("TRDAR_CD")) == area_code
        and str(r.get("SVC_INDUTY_CD")) == business_type
    ]
    q_sales_vals = [safe_int(r.get("THSMON_SELNG_AMT"))
                    for r in area_multi if safe_int(r.get("THSMON_SELNG_AMT")) > 0]

    if len(q_sales_vals) >= 2:
        avg_q = sum(q_sales_vals) / len(q_sales_vals)
        variance = sum((s - avg_q) ** 2 for s in q_sales_vals) / len(q_sales_vals)
        cv = (variance ** 0.5) / max(avg_q, 1)
        stability_score = _clamp(int(100 - cv * 200))
    else:
        stability_score = 50

    if vs_city_avg >= 120 and stability_score >= 60:
        grade = "우수"
    elif vs_city_avg >= 80 and stability_score >= 40:
        grade = "양호"
    elif vs_city_avg >= 50:
        grade = "보통"
    else:
        grade = "주의"

    biz_name = get_biz_name(business_type)

    recs = []
    if vs_city_avg >= 120:
        recs.append(f"서울 평균 대비 {vs_city_avg-100:.0f}% 높은 매출로 재무 상태가 양호합니다")
    elif vs_city_avg < 80:
        recs.append(f"서울 평균 대비 매출이 {100-vs_city_avg:.0f}% 낮아 매출 증대 전략이 필요합니다")

    if rent_grade == "과다":
        recs.append(f"매출 대비 임대료 비율이 {rent_ratio:.0f}%로 높아 임대료 부담이 큽니다")
    elif rent_grade == "주의":
        recs.append(f"임대료 비율이 {rent_ratio:.0f}%로 비용 관리에 주의가 필요합니다")

    if stability_score < 40:
        recs.append("매출 변동성이 높아 안정적 수익 확보 전략이 필요합니다")
    elif stability_score >= 70:
        recs.append("매출이 안정적으로 유지되고 있습니다")

    if profit_margin < 10:
        recs.append(f"원가와 임대료를 고려한 실질 수익률이 {profit_margin:.0f}%로 낮아 수익 개선이 시급합니다")

    return {
        "sales_per_store": sales_per_store,
        "city_avg_per_store": city_avg_per_store,
        "vs_city_avg": vs_city_avg,
        "estimated_monthly_revenue": sales_per_store,
        "estimated_monthly_cost": estimated_cost,
        "estimated_monthly_rent": estimated_rent,
        "estimated_profit": estimated_profit,
        "profit_margin": profit_margin,
        "cost_ratio": round(cost_ratio * 100, 1),
        "rent_ratio": rent_ratio,
        "rent_grade": rent_grade,
        "stability_score": stability_score,
        "grade": grade,
        "recommendation": ". ".join(recs) if recs else "재무 데이터가 부족합니다",
    }


# ── 9. 경영전략 추천 ──────────────────────────────────────

def compute_business_strategy(
    area_code: str,
    customer: dict,
    demand: dict,
    delivery: dict,
    menu_trend: dict,
    survival: dict,
    financial: dict,
    location_breakdown: list[dict],
    business_type: str = "CS100001",
) -> dict:
    biz_name = get_biz_name(business_type)

    strengths, weaknesses, opportunities, threats = [], [], [], []

    for b in location_breakdown:
        if b["score"] >= 70:
            strengths.append(f"{b['category']} 우수 ({b['score']}점)")
        elif b["score"] < 40:
            weaknesses.append(f"{b['category']} 부족 ({b['score']}점)")

    if customer.get("main_customer"):
        strengths.append(f"주요 고객: {customer['main_customer']}")

    if financial.get("vs_city_avg", 100) >= 120:
        strengths.append("서울 평균 대비 높은 매출")
    elif financial.get("vs_city_avg", 100) < 80:
        weaknesses.append("서울 평균 대비 낮은 매출")

    if financial.get("stability_score", 50) < 40:
        weaknesses.append("높은 매출 변동성")

    if delivery.get("delivery_score", 0) >= 60:
        opportunities.append("높은 배달 수요 잠재력")

    if menu_trend.get("growing_businesses"):
        top_grow = menu_trend["growing_businesses"][0]
        if top_grow.get("growth_rate", 0) > 10:
            opportunities.append(
                f"{top_grow['business_name']} 성장 트렌드 ({top_grow['growth_rate']}%)"
            )

    if survival.get("survival_3yr", 50) < 50:
        threats.append("낮은 3년 생존률")
    for risk in survival.get("risk_factors", []):
        threats.append(risk["factor"])

    strategies = []

    # 타겟 마케팅
    strategies.append({
        "title": "타겟 마케팅 전략",
        "description": (
            f"주 고객층인 {customer.get('main_customer', '30대')}를 타겟으로 한 맞춤형 마케팅. "
            f"피크 시간대({demand.get('peak_time', '')})에 집중 프로모션 운영"
        ),
        "priority": "high",
        "category": "마케팅",
    })

    # 시간대 전략
    strategies.append({
        "title": "시간대별 운영 전략",
        "description": (
            f"피크 시간대({demand.get('peak_time', '11-14시')})에 인력/재고 집중 배치. "
            f"주말 비중 {demand.get('weekend_ratio', 0)}%로 "
            + ("주말 영업 강화 필요" if demand.get("weekend_ratio", 0) > 40
               else "평일 집중 운영 추천")
        ),
        "priority": "high",
        "category": "운영",
    })

    # 배달 전략
    if delivery.get("delivery_score", 0) >= 50:
        times_str = ", ".join(delivery.get("recommended_times", [])[:2])
        strategies.append({
            "title": "배달 서비스 확대",
            "description": (
                f"배달 적합도 {delivery['delivery_score']}점. "
                f"추천 배달 시간: {times_str}. "
                + ("야간 배달도 검토하세요" if delivery.get("night_demand_ratio", 0) > 12 else "")
            ),
            "priority": "medium",
            "category": "채널",
        })

    # 비용 관리
    if financial.get("profit_margin", 40) < 40 or financial.get("vs_city_avg", 100) < 100:
        strategies.append({
            "title": "비용 최적화",
            "description": (
                f"예상 수익률 {financial.get('profit_margin', 0)}%. "
                f"원가율 {financial.get('cost_ratio', 60)}%로 "
                "식재료 공동구매, 메뉴 단순화 등 원가 절감 전략 추천"
            ),
            "priority": "high" if financial.get("profit_margin", 40) < 30 else "medium",
            "category": "재무",
        })

    # 경쟁 대응
    if menu_trend.get("competition_map"):
        high_comp = [c for c in menu_trend["competition_map"] if c["competition"] > 5]
        if high_comp:
            strategies.append({
                "title": "차별화 전략",
                "description": "동종 업종 경쟁이 치열합니다. 메뉴/서비스 차별화를 통해 경쟁 우위를 확보하세요",
                "priority": "high",
                "category": "경쟁",
            })

    # 리스크 관리
    if survival.get("survival_3yr", 50) < 60:
        risk_desc = ", ".join(r["factor"] for r in survival.get("risk_factors", [])[:2])
        strategies.append({
            "title": "리스크 관리",
            "description": (
                f"3년 생존율 {survival.get('survival_3yr', 0)}%. "
                + (f"주요 위험: {risk_desc}. " if risk_desc else "")
                + "비상 자금 확보 및 다각화 전략을 추천합니다"
            ),
            "priority": "high",
            "category": "리스크",
        })

    # 요약
    summary_parts = [f"[{biz_name}] 종합 경영전략:"]
    if strengths:
        summary_parts.append(f"강점({', '.join(strengths[:2])})을 활용하고")
    if weaknesses:
        summary_parts.append(f"약점({', '.join(weaknesses[:2])})을 보완하세요.")
    if opportunities:
        summary_parts.append(f"기회요인으로 {', '.join(opportunities[:2])}이(가) 있습니다.")
    if threats:
        summary_parts.append(f"위협요인({', '.join(threats[:2])})에 대비하세요.")

    return {
        "swot": {
            "strengths": strengths[:4],
            "weaknesses": weaknesses[:4],
            "opportunities": opportunities[:4],
            "threats": threats[:4],
        },
        "strategies": strategies,
        "summary": " ".join(summary_parts),
    }


# ── 10. 업종별 경영 팁 ────────────────────────────────────

# 업종별 기본 팁 (항상 표시)
_BASE_TIPS: dict[str, list[dict]] = {
    "CS100001": [  # 한식
        {"category": "메뉴", "title": "시그니처 메뉴 1~2개에 집중", "description": "메뉴가 많으면 재료 로스와 조리 시간이 늘어납니다. 대표 메뉴를 정하고 퀄리티를 극대화하세요."},
        {"category": "원가", "title": "식재료 로스율 관리", "description": "한식은 반찬 구성이 많아 로스율이 높습니다. 반찬 표준 레시피를 만들고 식재료 발주를 주 2~3회로 조절하세요."},
        {"category": "운영", "title": "점심·저녁 이모작 전략", "description": "백반 위주 점심 + 술안주 위주 저녁으로 시간대별 메뉴를 이원화하면 객단가를 높일 수 있습니다."},
        {"category": "마케팅", "title": "단골 관리 시스템", "description": "한식은 단골 비중이 높은 업종입니다. 적립/쿠폰 등 재방문 유도 장치를 마련하세요."},
    ],
    "CS100002": [  # 중식
        {"category": "메뉴", "title": "세트 구성으로 객단가 UP", "description": "짜장+탕수육 세트, 코스 구성 등 세트 메뉴로 객단가를 높이세요. 1인 세트도 트렌드입니다."},
        {"category": "배달", "title": "배달 포장 품질 관리", "description": "중식은 배달 비중이 높습니다. 면 불음 방지 포장, 소스 분리 포장 등 품질 유지에 투자하세요."},
        {"category": "원가", "title": "기름·소스 대량 구매", "description": "중식은 기름 사용량이 많습니다. 공동구매나 대용량 구매로 주요 원재료 원가를 절감하세요."},
    ],
    "CS100003": [  # 일식
        {"category": "메뉴", "title": "신선도가 곧 경쟁력", "description": "일식은 식재료 신선도가 매출에 직결됩니다. 안정적 수산물 공급처 확보가 최우선입니다."},
        {"category": "마케팅", "title": "비주얼 마케팅 활용", "description": "일식은 플레이팅이 중요합니다. 인스타그램 등 비주얼 중심 SNS 마케팅이 효과적입니다."},
        {"category": "운영", "title": "오마카세·코스 구성", "description": "트렌드인 오마카세/코스 구성을 도입하면 객단가와 예약률을 동시에 높일 수 있습니다."},
    ],
    "CS100004": [  # 양식
        {"category": "메뉴", "title": "런치 세트 필수 운영", "description": "양식은 객단가가 높아 점심 진입장벽이 있습니다. 합리적 런치 세트로 점심 고객을 확보하세요."},
        {"category": "마케팅", "title": "기념일·데이트 타겟", "description": "양식은 기념일 수요가 높습니다. 커플석/기념일 이벤트를 적극 홍보하세요."},
        {"category": "원가", "title": "와인·음료 마진 활용", "description": "양식은 음료(와인/칵테일) 마진이 높습니다. 페어링 추천으로 음료 매출을 높이세요."},
    ],
    "CS100005": [  # 제과점
        {"category": "운영", "title": "오전 생산·오후 할인", "description": "당일 생산·당일 판매 원칙을 지키되, 오후 5시 이후 할인으로 폐기를 줄이세요."},
        {"category": "마케팅", "title": "시즌 한정 메뉴 활용", "description": "시즌별 한정 메뉴(딸기·밤·크리스마스)는 화제성과 재방문을 동시에 잡을 수 있습니다."},
        {"category": "메뉴", "title": "기프트 박스/선물 세트", "description": "선물용 포장 옵션을 다양화하면 명절·기념일 매출을 크게 높일 수 있습니다."},
    ],
    "CS100006": [  # 패스트푸드
        {"category": "운영", "title": "주문·서빙 속도가 핵심", "description": "패스트푸드 고객은 속도를 기대합니다. 키오스크·모바일 주문으로 대기시간을 줄이세요."},
        {"category": "배달", "title": "배달앱 상위 노출 전략", "description": "배달앱 리뷰 관리와 쿠폰 프로모션으로 검색 상위 노출을 유지하세요."},
        {"category": "메뉴", "title": "사이드·세트 업셀링", "description": "감자튀김·음료 등 사이드 추가 유도로 객단가를 15~20% 높일 수 있습니다."},
    ],
    "CS100007": [  # 치킨
        {"category": "배달", "title": "배달 시간 30분 사수", "description": "치킨은 배달 시간이 곧 맛입니다. 30분 내 배달 가능한 반경을 설정하고 엄수하세요."},
        {"category": "마케팅", "title": "야간 프로모션 집중", "description": "치킨은 저녁~야간 수요가 80% 이상입니다. 20시 이후 할인·이벤트가 효과적입니다."},
        {"category": "메뉴", "title": "사이드 메뉴 다양화", "description": "떡볶이·감자·샐러드 등 사이드를 추가하면 세트 주문 비율과 객단가가 올라갑니다."},
    ],
    "CS100008": [  # 분식
        {"category": "원가", "title": "원가율 50% 이내 유지", "description": "분식은 박리다매 구조입니다. 식재료 원가를 50% 이내로 관리하는 것이 핵심입니다."},
        {"category": "운영", "title": "테이크아웃 비중 확대", "description": "좌석 회전율 한계를 테이크아웃으로 극복하세요. 포장 전용 메뉴 구성도 효과적입니다."},
        {"category": "메뉴", "title": "학생·직장인 세트", "description": "타겟 고객별 가성비 세트(학생 3,500원/직장인 5,000원)를 구성하면 충성 고객이 생깁니다."},
    ],
    "CS100009": [  # 호프/주점
        {"category": "운영", "title": "금·토 매출이 전체의 50%", "description": "주점은 금·토에 매출이 집중됩니다. 평일 이벤트(해피아워·반값데이)로 수요를 분산하세요."},
        {"category": "마케팅", "title": "2차 수요 잡기", "description": "주변 식당 밀집 지역이라면 '2차 맛집'을 컨셉으로 잡고 마감 시간을 늦추세요."},
        {"category": "메뉴", "title": "안주 퀄리티 = 재방문율", "description": "술보다 안주가 재방문을 결정합니다. 시그니처 안주 2~3개에 투자하세요."},
    ],
    "CS100010": [  # 커피/음료
        {"category": "운영", "title": "오전 7~9시 출근길 잡기", "description": "테이크아웃 커피 수요는 오전 7~9시에 집중됩니다. 빠른 서빙 체계를 갖추세요."},
        {"category": "마케팅", "title": "구독권/정기결제 도입", "description": "월 커피 구독권(예: 20잔 45,000원)은 고정 매출과 단골을 동시에 확보합니다."},
        {"category": "메뉴", "title": "비커피 메뉴 30% 이상", "description": "차·에이드·스무디 등 비커피 메뉴를 30% 이상 구성하면 고객층이 넓어집니다."},
        {"category": "원가", "title": "원두·시럽 직소싱", "description": "커피 원가율은 15~25%로 낮지만, 원두 직접 로스팅이나 산지 직소싱으로 차별화와 마진을 동시에 잡으세요."},
    ],
    "CS200001": [  # 의류
        {"category": "운영", "title": "시즌 전환 2주 전 세일", "description": "시즌 말 재고를 세일로 빠르게 소진하고, 신상품 입고 타이밍을 앞당기세요."},
        {"category": "마케팅", "title": "SNS 스타일링 콘텐츠", "description": "코디 제안 콘텐츠가 가장 효과적입니다. 주 3회 이상 스타일링 사진을 게시하세요."},
    ],
    "CS200002": [  # 미용실
        {"category": "마케팅", "title": "비포/애프터 포트폴리오", "description": "시술 전후 사진은 가장 강력한 마케팅 도구입니다. 고객 동의를 얻어 꾸준히 축적하세요."},
        {"category": "운영", "title": "예약제 + 노쇼 관리", "description": "예약 부도율이 높은 업종입니다. 예약금 제도나 리마인드 문자로 노쇼를 줄이세요."},
        {"category": "메뉴", "title": "멤버십·패키지 상품", "description": "커트+펌+컬러 패키지를 할인가로 묶으면 객단가와 재방문율이 동시에 올라갑니다."},
    ],
    "CS200003": [  # 편의점
        {"category": "운영", "title": "발주 정확도가 수익률", "description": "편의점 수익은 발주에서 결정됩니다. POS 데이터 기반으로 요일·시간대별 발주량을 최적화하세요."},
        {"category": "운영", "title": "카테고리별 진열 최적화", "description": "음료·간식은 눈높이에, 도시락은 입구 근처에 배치하면 충동구매율이 올라갑니다."},
    ],
    "CS200004": [  # 슈퍼마켓
        {"category": "원가", "title": "로컬 직거래 비중 확대", "description": "중간 유통을 줄이고 산지/로컬 농가 직거래를 늘리면 마진과 신선도를 동시에 확보합니다."},
        {"category": "마케팅", "title": "요일별 특가 운영", "description": "수요일 채소 특가, 금요일 생선 특가 등 요일 특가로 정기 방문 패턴을 만드세요."},
    ],
    "CS200005": [  # 의약품
        {"category": "마케팅", "title": "건강 상담 서비스 강화", "description": "약사 상담 품질이 곧 차별화입니다. 건강 상담 코너를 운영하면 충성 고객이 생깁니다."},
        {"category": "운영", "title": "계절 질환 미리 대응", "description": "환절기 감기약, 여름 모기약 등 계절 수요를 2주 전에 미리 비축하세요."},
    ],
}

# 범용 팁 (업종 무관)
_GENERIC_TIPS = [
    {"category": "마케팅", "title": "네이버 플레이스 관리 필수", "description": "네이버 플레이스 사진·영업시간·메뉴를 최신으로 유지하세요. 리뷰 답글도 꼼꼼히 달면 검색 노출이 올라갑니다."},
    {"category": "마케팅", "title": "구글 비즈니스 프로필 등록", "description": "외국인 고객이나 지도 검색 유입을 위해 구글 비즈니스 프로필도 등록하세요."},
    {"category": "재무", "title": "월 고정비 체크리스트", "description": "임대료·인건비·공과금·보험을 매월 정리하세요. 매출의 70% 이내로 고정비를 유지하는 것이 안전합니다."},
    {"category": "재무", "title": "비상 운영자금 3개월분 확보", "description": "매출 급감에 대비해 최소 3개월치 고정비를 비상금으로 확보해두세요."},
]


def compute_business_tips(
    business_type: str,
    customer: dict,
    demand: dict,
    delivery: dict,
    financial: dict,
    survival: dict,
) -> list[dict]:
    """업종별 + 상황별 맞춤 경영 팁"""
    tips: list[dict] = []

    # 1) 업종 기본 팁
    base = _BASE_TIPS.get(business_type, [])
    for t in base:
        tips.append({**t, "source": "업종 특화"})

    # 2) 상황별 동적 팁
    # 고객 기반 팁
    main_age = customer.get("main_customer", "")
    if "20대" in main_age or "30대" in main_age:
        tips.append({
            "category": "마케팅",
            "title": "SNS·인플루언서 마케팅 추천",
            "description": f"이 상권의 주 고객층은 {main_age}입니다. 인스타그램 릴스, 틱톡 등 숏폼 콘텐츠가 효과적입니다.",
            "source": "고객 분석",
        })
    elif "50대" in main_age or "60대" in main_age:
        tips.append({
            "category": "마케팅",
            "title": "전단지·지역 커뮤니티 활용",
            "description": f"이 상권의 주 고객층은 {main_age}입니다. 오프라인 전단지와 지역 밴드/카페 홍보가 효과적입니다.",
            "source": "고객 분석",
        })

    if customer.get("female_ratio", 50) > 60:
        tips.append({
            "category": "운영",
            "title": "여성 고객 편의시설 강화",
            "description": "여성 고객 비중이 높습니다. 파우더룸, 깔끔한 화장실, 충전 콘센트 등 편의시설을 챙기세요.",
            "source": "고객 분석",
        })

    # 시간대 기반 팁
    peak = demand.get("peak_time", "")
    if "17-21" in peak:
        tips.append({
            "category": "운영",
            "title": "저녁 피크 대비 인력 배치",
            "description": "17~21시 수요가 가장 높습니다. 이 시간대에 서빙·주방 인력을 집중 배치하세요.",
            "source": "수요 분석",
        })
    elif "11-14" in peak:
        tips.append({
            "category": "메뉴",
            "title": "점심 특선 구성",
            "description": "점심 수요가 가장 높습니다. 빠르게 제공 가능한 점심 특선/세트를 운영하세요.",
            "source": "수요 분석",
        })

    if demand.get("weekend_ratio", 0) > 45:
        tips.append({
            "category": "운영",
            "title": "주말 영업 전략 강화",
            "description": f"주말 수요 비중이 {demand.get('weekend_ratio', 0)}%입니다. 주말 한정 메뉴나 프로모션을 운영하세요.",
            "source": "수요 분석",
        })

    # 배달 기반 팁
    if delivery.get("delivery_score", 0) >= 60:
        tips.append({
            "category": "배달",
            "title": "배달 전용 메뉴 개발",
            "description": "배달 적합도가 높은 상권입니다. 배달에 최적화된 전용 메뉴(용기 친화적, 식지 않는 메뉴)를 개발하세요.",
            "source": "배달 분석",
        })
    if delivery.get("night_demand_ratio", 0) > 15:
        tips.append({
            "category": "배달",
            "title": "야식 메뉴 추가",
            "description": f"야간 수요가 {delivery.get('night_demand_ratio', 0)}%입니다. 야식용 간편 메뉴를 추가하면 매출을 높일 수 있습니다.",
            "source": "배달 분석",
        })

    # 재무 기반 팁
    if financial.get("vs_city_avg", 100) < 80:
        tips.append({
            "category": "재무",
            "title": "매출 부진 극복 전략",
            "description": "서울 평균 대비 매출이 낮습니다. 가격 인하보다 가성비 세트 구성, SNS 이벤트 등으로 신규 고객을 유치하세요.",
            "source": "재무 분석",
        })
    if financial.get("stability_score", 50) < 40:
        tips.append({
            "category": "재무",
            "title": "매출 안정화 필요",
            "description": "매출 변동이 큽니다. 정기 이벤트, 구독 서비스, 단골 프로그램으로 기본 매출을 안정시키세요.",
            "source": "재무 분석",
        })

    # 생존 기반 팁
    if survival.get("survival_3yr", 50) < 50:
        tips.append({
            "category": "재무",
            "title": "생존율 낮은 지역 주의",
            "description": "이 상권의 3년 생존율이 낮습니다. 초기 투자를 최소화하고, 고정비를 줄이는 린(Lean) 창업 전략을 추천합니다.",
            "source": "생존 분석",
        })

    # 3) 범용 팁 추가 (최대 2개)
    for t in _GENERIC_TIPS[:2]:
        tips.append({**t, "source": "공통"})

    return tips
