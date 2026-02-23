import logging
from fastapi import APIRouter, Query, HTTPException, Request
from models.schemas import AreaSummary, AreaDetail
import asyncio
from services.data_processor import area_to_summary, safe_int, classify_district_type, BUSINESS_TYPES, AREA_TYPE_MAP, compute_batch_scores

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/areas", response_model=list[AreaSummary])
async def list_areas(
    request: Request,
    search: str = Query(None, description="상권명/자치구 검색"),
    area_type: str = Query(None, description="상권유형 (골목상권/발달상권/전통시장/관광특구)"),
    district: str = Query(None, description="자치구 필터"),
    business_type: str = Query(None, description="업종 코드 (점수 계산용)"),
    limit: int = Query(500, le=2000),
):
    """상권 목록 조회 (업종별 점수 반영)"""
    client = request.app.state.seoul_client
    raw_areas = await client.get_areas()

    summaries = [area_to_summary(a) for a in raw_areas]

    if search:
        sl = search.lower()
        summaries = [s for s in summaries if sl in s["name"].lower() or sl in s["district"].lower()]

    if area_type:
        summaries = [s for s in summaries if s["area_type"] == area_type]

    if district:
        summaries = [s for s in summaries if s["district"] == district]

    summaries = summaries[:limit]

    # 업종별 점수 계산
    if business_type and summaries:
        area_codes = [s["code"] for s in summaries]
        try:
            sales_data = await client.get_sales("20253")
            pop_data = await client.get_floating_pop("20253")
            store_data = await client.get_stores("20253")

            scores = compute_batch_scores(area_codes, sales_data, pop_data, store_data, business_type)
            for s in summaries:
                s["score"] = scores.get(s["code"], 50)
        except Exception as e:
            logger.warning(f"Failed to compute batch scores: {e}")

    return [AreaSummary(**s) for s in summaries]


@router.get("/areas/{code}", response_model=AreaDetail)
async def area_detail(request: Request, code: str):
    """상권 상세 정보"""
    client = request.app.state.seoul_client

    area_info = client.get_area_info(code)
    if not area_info:
        raise HTTPException(404, "상권을 찾을 수 없습니다")

    summary = area_to_summary(area_info)

    # 병렬 데이터 로드
    pop_data, store_data, sales_data, worker_pop_data, resident_pop_data = await asyncio.gather(
        client.get_floating_pop("20253"),
        client.get_stores("20253"),
        client.get_sales("20253"),
        client.get_worker_pop("20253"),
        client.get_resident_pop("20253"),
    )

    area_pop = [r for r in pop_data if str(r.get("TRDAR_CD")) == code]
    floating_pop = safe_int(area_pop[0].get("TOT_FLPOP_CO")) if area_pop else 0

    area_stores = [r for r in store_data if str(r.get("TRDAR_CD")) == code]
    store_count = sum(safe_int(r.get("STOR_CO")) for r in area_stores)

    area_sales = [r for r in sales_data if str(r.get("TRDAR_CD")) == code]
    avg_sales = 0
    if area_sales:
        avg_sales = sum(safe_int(r.get("THSMON_SELNG_AMT")) for r in area_sales) // len(area_sales)

    # 지구유형 분류
    dt = classify_district_type(code, worker_pop_data, resident_pop_data)

    return AreaDetail(
        **summary,
        floating_pop=floating_pop,
        resident_pop=dt["resident_pop"],
        worker_pop=dt["worker_pop"],
        district_type=dt["district_type"],
        worker_resident_ratio=dt["ratio"],
        household=dt["household"],
        store_count=store_count,
        avg_monthly_sales=avg_sales,
    )


@router.get("/business-types")
async def get_business_types():
    """업종 목록"""
    return BUSINESS_TYPES


@router.get("/area-types")
async def get_area_types():
    """상권유형 목록"""
    return [{"code": k, "name": v} for k, v in AREA_TYPE_MAP.items()]
