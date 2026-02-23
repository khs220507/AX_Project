import asyncio
from fastapi import APIRouter, Query, HTTPException, Request
from models.schemas import TrendsResponse, QuarterlyTrend
from services.data_processor import safe_int, RECENT_QUARTERS, get_biz_name

router = APIRouter(prefix="/api")


def _parse_yyqu(yyqu: str) -> str:
    """'20253' → '2025-Q3'"""
    if len(yyqu) == 5:
        return f"{yyqu[:4]}-Q{yyqu[4]}"
    return yyqu


@router.get("/trends/{code}", response_model=TrendsResponse)
async def get_trends(
    request: Request,
    code: str,
    business_type: str = Query("CS100001", description="업종 코드"),
):
    """상권 트렌드 (분기별 매출/인구 시계열)"""
    client = request.app.state.seoul_client

    area_info = client.get_area_info(code)
    if not area_info:
        raise HTTPException(404, "상권을 찾을 수 없습니다")

    # 모든 분기 데이터를 병렬로 프리페치
    sales_tasks = [client.get_sales(yyqu) for yyqu in RECENT_QUARTERS]
    pop_tasks = [client.get_floating_pop(yyqu) for yyqu in RECENT_QUARTERS]
    store_tasks = [client.get_stores(yyqu) for yyqu in RECENT_QUARTERS]

    all_results = await asyncio.gather(*sales_tasks, *pop_tasks, *store_tasks)

    n = len(RECENT_QUARTERS)
    sales_by_q = all_results[:n]
    pop_by_q = all_results[n:2*n]
    store_by_q = all_results[2*n:]

    quarters = []
    for i, yyqu in enumerate(RECENT_QUARTERS):
        sales_data = sales_by_q[i]
        pop_data = pop_by_q[i]
        store_data = store_by_q[i]

        area_sales = [
            r for r in sales_data
            if str(r.get("TRDAR_CD")) == code
            and str(r.get("SVC_INDUTY_CD")) == business_type
        ]
        sales = safe_int(area_sales[0].get("THSMON_SELNG_AMT")) if area_sales else 0

        area_pop = [r for r in pop_data if str(r.get("TRDAR_CD")) == code]
        floating_pop = safe_int(area_pop[0].get("TOT_FLPOP_CO")) if area_pop else 0

        area_stores = [
            r for r in store_data
            if str(r.get("TRDAR_CD")) == code
            and str(r.get("SVC_INDUTY_CD")) == business_type
        ]
        store_count = safe_int(area_stores[0].get("STOR_CO")) if area_stores else 0

        if sales > 0 or floating_pop > 0:
            quarters.append(QuarterlyTrend(
                quarter=_parse_yyqu(yyqu),
                sales=sales,
                floating_pop=floating_pop,
                resident_pop=0,
                worker_pop=0,
                store_count=store_count,
            ))

    return TrendsResponse(
        area_code=code,
        area_name=area_info["name"],
        business_type=get_biz_name(business_type),
        quarters=quarters,
    )
