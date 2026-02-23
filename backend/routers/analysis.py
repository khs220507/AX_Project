import asyncio
from fastapi import APIRouter, Query, HTTPException, Request
from models.schemas import AnalysisResponse, ScoreBreakdownItem, BizRecommendation, ClosureStats, DistrictTypeInfo
from services.data_processor import (
    compute_location_score, generate_grade, generate_recommendation,
    get_biz_name, recommend_missing_businesses, compute_closure_stats,
    classify_district_type, RECENT_QUARTERS,
)

router = APIRouter(prefix="/api")


@router.get("/analysis/{code}", response_model=AnalysisResponse)
async def get_analysis(
    request: Request,
    code: str,
    business_type: str = Query("CS100001", description="업종 코드"),
):
    """상권 입지분석 + 미진출 업종 추천"""
    client = request.app.state.seoul_client

    area_info = client.get_area_info(code)
    if not area_info:
        raise HTTPException(404, "상권을 찾을 수 없습니다")

    # 최신 분기 데이터 수집 (병렬)
    sales_task = client.get_sales("20253")
    pop_task = client.get_floating_pop("20253")
    store_task = client.get_stores("20253")
    facility_task = client.get_facilities("20253")
    change_idx_task = client.get_change_index("20253")
    worker_pop_task = client.get_worker_pop("20253")
    resident_pop_task = client.get_resident_pop("20253")

    other_store_tasks = {
        yyqu: client.get_stores(yyqu)
        for yyqu in RECENT_QUARTERS if yyqu != "20253"
    }

    sales_data, pop_data, store_data, facility_data, change_idx_data, worker_pop_data, resident_pop_data, *other_results = await asyncio.gather(
        sales_task, pop_task, store_task, facility_task, change_idx_task,
        worker_pop_task, resident_pop_task,
        *other_store_tasks.values(),
    )

    store_data_by_quarter: dict[str, list[dict]] = {"20253": store_data}
    for yyqu, data in zip(other_store_tasks.keys(), other_results):
        store_data_by_quarter[yyqu] = data

    score_result = compute_location_score(
        code, sales_data, pop_data, store_data,
        facility_data=facility_data,
        change_idx_data=change_idx_data,
    )

    total_score = score_result["total_score"]
    grade = generate_grade(total_score)
    biz_name = get_biz_name(business_type)

    breakdown_items = [
        ScoreBreakdownItem(
            category=b["category"],
            score=b["score"],
            rank_pct=round(100 - b["score"], 1),
        )
        for b in score_result["breakdown"]
    ]

    recommendation = generate_recommendation(
        area_info["name"], score_result["breakdown"], grade, biz_name
    )

    # 폐업률 산출
    closure_raw = compute_closure_stats(code, store_data_by_quarter)
    closure_stats = ClosureStats(**closure_raw)

    # 지구유형 분류
    dt = classify_district_type(code, worker_pop_data, resident_pop_data)
    district_info = DistrictTypeInfo(**dt)

    # 미진출 업종 추천
    missing_recs = recommend_missing_businesses(code, sales_data, store_data, pop_data)
    biz_recs = [BizRecommendation(**r) for r in missing_recs]

    return AnalysisResponse(
        area_code=code,
        area_name=area_info["name"],
        business_type=biz_name,
        total_score=total_score,
        grade=grade,
        breakdown=breakdown_items,
        recommendation=recommendation,
        district_info=district_info,
        closure_stats=closure_stats,
        missing_biz_recommendations=biz_recs,
    )
