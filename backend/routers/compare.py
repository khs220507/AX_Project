from fastapi import APIRouter, Query, HTTPException, Request
from models.schemas import (
    CompareResponse, CompareArea, AreaSummary,
    ScoreBreakdownItem, BusinessTypeSales,
)
from services.data_processor import (
    compute_location_score, area_to_summary, safe_int, get_biz_name,
)

router = APIRouter(prefix="/api")


@router.get("/compare", response_model=CompareResponse)
async def compare_areas(
    request: Request,
    codes: str = Query(..., description="쉼표로 구분된 상권코드 (2~3개)"),
):
    """상권 비교"""
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if len(code_list) < 2 or len(code_list) > 3:
        raise HTTPException(400, "2~3개의 상권코드를 입력해주세요")

    client = request.app.state.seoul_client

    sales_data = await client.get_sales("20253")
    pop_data = await client.get_floating_pop("20252")
    store_data = await client.get_stores("20253")

    result_areas = []

    for code in code_list:
        area_info = client.get_area_info(code)
        if not area_info:
            raise HTTPException(404, f"상권 {code}을(를) 찾을 수 없습니다")

        summary = area_to_summary(area_info)
        score_result = compute_location_score(code, sales_data, pop_data, store_data)
        summary["score"] = score_result["total_score"]

        breakdown = [
            ScoreBreakdownItem(
                category=b["category"],
                score=b["score"],
                rank_pct=round(100 - b["score"], 1),
            )
            for b in score_result["breakdown"]
        ]

        # 업종별 매출 (상위 5개)
        area_sales = [r for r in sales_data if str(r.get("TRDAR_CD")) == code]
        biz_map: dict[str, list[int]] = {}
        for r in area_sales:
            bc = str(r.get("SVC_INDUTY_CD", ""))
            biz_map.setdefault(bc, []).append(safe_int(r.get("THSMON_SELNG_AMT")))

        top_biz = []
        for bc, vals in sorted(biz_map.items(), key=lambda x: sum(x[1]), reverse=True)[:5]:
            top_biz.append(BusinessTypeSales(
                business_type=get_biz_name(bc),
                avg_sales=sum(vals) // len(vals),
                store_count=0,
            ))

        result_areas.append(CompareArea(
            area=AreaSummary(**summary),
            breakdown=breakdown,
            top_businesses=top_biz,
        ))

    return CompareResponse(areas=result_areas)
