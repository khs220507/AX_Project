import logging
from .data_processor import safe_int

logger = logging.getLogger(__name__)


def predict_sales(
    historical_sales: list[dict],
    area_code: str,
    business_type_code: str,
    model_manager=None,
    pop_by_q: dict | None = None,
    sales_by_q: dict | None = None,
    store_by_q: dict | None = None,
) -> dict:
    """과거 매출 데이터 기반 다음 분기 매출 예측 (PyTorch LSTM 우선, fallback: 선형회귀)"""

    # PyTorch LSTM 모델 시도
    if model_manager and model_manager.is_ready("sales_lstm") and pop_by_q and sales_by_q and store_by_q:
        try:
            result = model_manager.predict_sales_lstm(
                area_code, business_type_code, pop_by_q, sales_by_q, store_by_q,
            )
            if result:
                result["model_used"] = "LSTM"
                return result
        except Exception as e:
            logger.warning(f"LSTM prediction failed, falling back: {e}")

    # 기존 선형회귀 fallback
    # 해당 상권+업종의 분기별 매출 추출
    filtered = [
        r for r in historical_sales
        if str(r.get("TRDAR_CD")) == area_code
        and str(r.get("SVC_INDUTY_CD")) == business_type_code
    ]

    # 분기별로 정렬
    filtered.sort(key=lambda r: (
        safe_int(r.get("STDR_YR_CD")),
        safe_int(r.get("STDR_QU_CD")),
    ))

    if len(filtered) < 2:
        return _empty_prediction(area_code, business_type_code)

    # 분기별 매출 시계열
    quarterly = []
    for r in filtered:
        year = safe_int(r.get("STDR_YR_CD"))
        quarter = safe_int(r.get("STDR_QU_CD"))
        sales = safe_int(r.get("THSMON_SELNG_AMT"))
        if year > 0 and quarter > 0 and sales > 0:
            quarterly.append({
                "year": year,
                "quarter": quarter,
                "label": f"{year}-Q{quarter}",
                "sales": sales,
            })

    if len(quarterly) < 2:
        return _empty_prediction(area_code, business_type_code)

    sales_values = [q["sales"] for q in quarterly]
    n = len(sales_values)

    # 단순 선형회귀
    sum_x = sum(range(n))
    sum_y = sum(sales_values)
    sum_xy = sum(i * y for i, y in enumerate(sales_values))
    sum_x2 = sum(i * i for i in range(n))

    denom = n * sum_x2 - sum_x * sum_x
    if denom == 0:
        slope = 0
        intercept = sum_y / n
    else:
        slope = (n * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / n

    # 계절성 계수 (분기별 평균 비율)
    seasonal = {1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0}
    if n >= 4:
        q_sums = {1: [], 2: [], 3: [], 4: []}
        for q in quarterly:
            q_sums[q["quarter"]].append(q["sales"])
        overall_avg = sum(sales_values) / n
        for qnum, vals in q_sums.items():
            if vals and overall_avg > 0:
                seasonal[qnum] = (sum(vals) / len(vals)) / overall_avg

    # 현재 분기 정보
    last = quarterly[-1]
    current_sales = last["sales"]

    # 다음 4분기 예측
    predictions = []
    last_year = last["year"]
    last_q = last["quarter"]

    for step in range(1, 5):
        next_q = (last_q + step - 1) % 4 + 1
        next_year = last_year + (last_q + step - 1) // 4

        trend_value = intercept + slope * (n + step - 1)
        season_factor = seasonal.get(next_q, 1.0)
        predicted = max(0, int(trend_value * season_factor))

        margin_pct = 0.08 + 0.04 * (step - 1)  # 8%~20% 증가
        lower = max(0, int(predicted * (1 - margin_pct)))
        upper = int(predicted * (1 + margin_pct))

        predictions.append({
            "quarter": f"{next_year}-Q{next_q}",
            "predicted": predicted,
            "lower": lower,
            "upper": upper,
        })

    # 성장률
    next_pred = predictions[0]["predicted"]
    growth_rate = ((next_pred - current_sales) / max(current_sales, 1)) * 100

    # 영향 요인 분석
    factors = _analyze_factors(slope, seasonal, last_q, growth_rate)

    return {
        "area_code": area_code,
        "business_type": business_type_code,
        "current_quarter_sales": current_sales,
        "predicted_next_quarter": next_pred,
        "growth_rate": round(growth_rate, 1),
        "confidence_lower": predictions[0]["lower"],
        "confidence_upper": predictions[0]["upper"],
        "quarterly_predictions": predictions,
        "factors": factors,
        "historical": [
            {"quarter": q["label"], "sales": q["sales"]} for q in quarterly
        ],
        "model_used": "linear_regression",
    }


def _analyze_factors(slope: float, seasonal: dict, current_q: int, growth_rate: float) -> list[dict]:
    """예측 영향 요인 분석"""
    factors = []

    if slope > 0:
        factors.append({"name": "매출 상승 추세", "impact": f"+{min(abs(growth_rate) * 0.4, 15):.1f}%"})
    elif slope < 0:
        factors.append({"name": "매출 하락 추세", "impact": f"-{min(abs(growth_rate) * 0.4, 15):.1f}%"})

    next_q = current_q % 4 + 1
    season_effect = (seasonal.get(next_q, 1.0) - 1.0) * 100
    if abs(season_effect) > 1:
        name = "계절 효과" + (" (성수기)" if season_effect > 0 else " (비수기)")
        sign = "+" if season_effect > 0 else ""
        factors.append({"name": name, "impact": f"{sign}{season_effect:.1f}%"})

    return factors


def _empty_prediction(area_code: str, business_type_code: str) -> dict:
    """데이터 부족 시 빈 예측 결과"""
    return {
        "area_code": area_code,
        "business_type": business_type_code,
        "current_quarter_sales": 0,
        "predicted_next_quarter": 0,
        "growth_rate": 0.0,
        "confidence_lower": 0,
        "confidence_upper": 0,
        "quarterly_predictions": [],
        "factors": [{"name": "데이터 부족", "impact": "예측 불가"}],
        "historical": [],
    }
