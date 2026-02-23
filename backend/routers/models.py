import asyncio
from fastapi import APIRouter, Query, HTTPException, Request
from models.schemas import AdvancedModelsResponse
from services.data_processor import (
    compute_location_score, get_biz_name, guess_district, RECENT_QUARTERS,
)
from services.advanced_models import (
    compute_demand_analysis,
    compute_customer_profile,
    compute_delivery_optimization,
    compute_menu_trend,
    compute_survival_prediction,
    compute_financial_diagnosis,
    compute_business_strategy,
    compute_business_tips,
)

router = APIRouter(prefix="/api")


@router.get("/models/{code}", response_model=AdvancedModelsResponse)
async def get_advanced_models(
    request: Request,
    code: str,
    business_type: str = Query("CS100001", description="업종 코드"),
):
    """고급 분석 모델 7종 (수요예측·고객특성·배달최적화·메뉴트렌드·생존예측·재무진단·경영전략)"""
    client = request.app.state.seoul_client

    area_info = client.get_area_info(code)
    if not area_info:
        raise HTTPException(404, "상권을 찾을 수 없습니다")

    # 데이터 수집 (병렬)
    sales_task = client.get_sales("20253")
    pop_task = client.get_floating_pop("20253")
    store_task = client.get_stores("20253")
    facility_task = client.get_facilities("20253")
    change_idx_task = client.get_change_index("20253")

    # 다중 분기 매출 + 분기별 점포 데이터도 병렬로
    multi_q_tasks = [client.get_sales(yyqu) for yyqu in RECENT_QUARTERS[-4:]]
    other_store_tasks = {
        yyqu: client.get_stores(yyqu)
        for yyqu in RECENT_QUARTERS if yyqu != "20253"
    }

    sales_data, pop_data, store_data, facility_data, change_idx_data, *multi_q_results = await asyncio.gather(
        sales_task, pop_task, store_task, facility_task, change_idx_task,
        *multi_q_tasks,
    )
    multi_q_sales = [row for rows in multi_q_results for row in rows]

    # 분기별 점포 데이터 병렬 로드
    other_store_keys = list(other_store_tasks.keys())
    other_store_results = await asyncio.gather(*other_store_tasks.values())

    store_data_by_quarter: dict[str, list[dict]] = {"20253": store_data}
    for yyqu, data in zip(other_store_keys, other_store_results):
        store_data_by_quarter[yyqu] = data

    # 입지 분석 (경영전략에서 필요)
    score_result = compute_location_score(
        code, sales_data, pop_data, store_data,
        facility_data=facility_data,
        change_idx_data=change_idx_data,
    )

    biz_name = get_biz_name(business_type)

    # 7개 모델 실행
    demand = compute_demand_analysis(code, pop_data, sales_data)
    customer = compute_customer_profile(code, pop_data, sales_data)
    delivery = compute_delivery_optimization(code, pop_data, sales_data, store_data)
    menu_trend = compute_menu_trend(code, sales_data, store_data, multi_q_sales)
    model_manager = getattr(request.app.state, "model_manager", None)
    survival = compute_survival_prediction(
        code, store_data, store_data_by_quarter, pop_data, sales_data,
        model_manager=model_manager, facility_data=facility_data,
    )
    district = guess_district(area_info.get("name", ""))
    financial = compute_financial_diagnosis(
        code, sales_data, store_data, multi_q_sales, business_type,
        district=district,
    )
    strategy = compute_business_strategy(
        code, customer, demand, delivery, menu_trend,
        survival, financial, score_result["breakdown"], business_type
    )

    tips = compute_business_tips(
        business_type, customer, demand, delivery, financial, survival
    )

    return AdvancedModelsResponse(
        area_code=code,
        area_name=area_info["name"],
        business_type=biz_name,
        demand=demand,
        customer=customer,
        delivery=delivery,
        menu_trend=menu_trend,
        survival=survival,
        financial=financial,
        strategy=strategy,
        tips=tips,
    )
