from fastapi import APIRouter, Query, Request
from models.schemas import PolicyResponse
from config import get_settings
from services.policy_service import (
    fetch_bizinfo_policies,
    get_fallback_policies,
    match_policies_to_business,
)

router = APIRouter(prefix="/api")


@router.get("/policies", response_model=PolicyResponse)
async def get_policies(
    request: Request,
    business_type: str = Query("CS100010", description="업종 코드"),
):
    """소상공인 정부 지원정책 조회 (Bizinfo API 또는 정적 데이터)"""
    settings = get_settings()
    source = "static"
    policies: list[dict] = []

    if settings.BIZINFO_API_KEY:
        policies = await fetch_bizinfo_policies(settings.BIZINFO_API_KEY)
        if policies:
            source = "bizinfo"

    if not policies:
        policies = get_fallback_policies()

    matched = match_policies_to_business(policies, business_type)

    biz_categories = {
        "CS100001": "음식점", "CS100002": "음식점", "CS100003": "음식점",
        "CS100004": "음식점", "CS100005": "음식점", "CS100006": "음식점",
        "CS100007": "음식점", "CS100008": "음식점", "CS100009": "음식점",
        "CS100010": "음식점",
        "CS200001": "소매업", "CS200002": "서비스업",
        "CS200003": "소매업", "CS200004": "소매업", "CS200005": "소매업",
    }

    return PolicyResponse(
        total_count=len(matched),
        policies=matched,
        source=source,
        matched_category=biz_categories.get(business_type, "소상공인"),
    )
