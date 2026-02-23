import json
import logging
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, Query, Request, HTTPException

from models.schemas import (
    RegionInfo,
    DongSummary,
    NationwideAnalysisResponse,
    ScoreBreakdownItem,
    StoreSummary,
    CategoryCount,
    BizRecommendation,
)
from services.nationwide_processor import (
    SIDO_LIST,
    SIDO_MAP,
    compute_dong_scores,
    compute_store_analysis,
    recommend_missing_businesses_nationwide,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# GeoJSON 디렉토리
GEOJSON_DIR = Path(__file__).parent.parent / "data" / "geojson"

# 시도 코드 → GeoJSON 파일명 매핑
SIDO_GEOJSON_MAP = {
    "11": "hangjeongdong_서울특별시.geojson",
    "26": "hangjeongdong_부산광역시.geojson",
    "27": "hangjeongdong_대구광역시.geojson",
    "28": "hangjeongdong_인천광역시.geojson",
    "29": "hangjeongdong_광주광역시.geojson",
    "30": "hangjeongdong_대전광역시.geojson",
    "31": "hangjeongdong_울산광역시.geojson",
    "36": "hangjeongdong_세종특별자치시.geojson",
    "41": "hangjeongdong_경기도.geojson",
    "42": "hangjeongdong_강원도.geojson",
    "43": "hangjeongdong_충청북도.geojson",
    "44": "hangjeongdong_충청남도.geojson",
    "45": "hangjeongdong_전라북도.geojson",
    "46": "hangjeongdong_전라남도.geojson",
    "47": "hangjeongdong_경상북도.geojson",
    "48": "hangjeongdong_경상남도.geojson",
    "50": "hangjeongdong_제주특별자치도.geojson",
}

# GeoJSON 캐시 (동 코드 목록)
_geojson_dong_cache: dict[str, list[dict]] = {}


def _load_dong_list(sido_code: str) -> list[dict]:
    """GeoJSON에서 동 코드/이름 목록 추출 (캐시)"""
    if sido_code in _geojson_dong_cache:
        return _geojson_dong_cache[sido_code]

    filename = SIDO_GEOJSON_MAP.get(sido_code)
    if not filename:
        return []

    filepath = GEOJSON_DIR / filename
    if not filepath.exists():
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            geojson = json.load(f)
        dong_list = []
        for feature in geojson.get("features", []):
            props = feature.get("properties", {})
            dong_list.append({
                "adm_cd": props.get("adm_cd", ""),
                "adm_nm": props.get("adm_nm", ""),
                "sggnm": props.get("sggnm", ""),
            })
        _geojson_dong_cache[sido_code] = dong_list
        return dong_list
    except Exception as e:
        logger.error(f"Failed to load GeoJSON for {sido_code}: {e}")
        return []


@router.get("/regions")
async def list_regions() -> list[RegionInfo]:
    """17개 시도 목록"""
    return [RegionInfo(**s) for s in SIDO_LIST]


@router.get("/regions/{sido_code}/dongs")
async def get_region_dongs(
    request: Request,
    sido_code: str,
    business_type: str = Query(None, description="업종 코드"),
):
    """시도별 동 점포밀도 데이터"""
    if sido_code == "11":
        return {"redirect": "seoul", "message": "서울은 /api/areas 엔드포인트를 사용하세요"}

    sido_info = SIDO_MAP.get(sido_code)
    if not sido_info:
        raise HTTPException(404, "해당 시도를 찾을 수 없습니다")

    semas_client = getattr(request.app.state, "semas_client", None)
    if not semas_client:
        raise HTTPException(503, "SEMAS API 클라이언트가 초기화되지 않았습니다. DATA_GO_KR_API_KEY를 설정하세요.")

    # GeoJSON에서 동 목록 가져오기
    dong_list = _load_dong_list(sido_code)
    if not dong_list:
        raise HTTPException(404, "해당 시도의 GeoJSON 데이터가 없습니다")

    # 시군구별로 점포 조회 (동별 개별 조회보다 효율적)
    # 시도 코드로 시작하는 시군구 코드 그룹핑
    signgu_codes = set()
    for dong in dong_list:
        adm_cd = dong.get("adm_cd", "")
        if len(adm_cd) >= 5:
            signgu_codes.add(adm_cd[:5])

    # 시군구별로 점포 조회 후 동별로 분류
    stores_by_dong: dict[str, list[dict]] = defaultdict(list)
    for signgu_cd in list(signgu_codes)[:30]:  # 최대 30개 시군구
        try:
            stores = await semas_client.get_stores_in_signgu(signgu_cd)
            for store in stores:
                adong_cd = store.get("adongCd", "")
                if adong_cd:
                    stores_by_dong[adong_cd].append(store)
        except Exception as e:
            logger.warning(f"Failed to fetch stores for signgu {signgu_cd}: {e}")

    # 동별 점수 계산
    dong_scores = compute_dong_scores(stores_by_dong, business_type)

    # GeoJSON 동 목록과 점수 매핑
    result: list[DongSummary] = []
    for dong in dong_list:
        adm_cd = dong.get("adm_cd", "")
        # adm_cd(8자리)와 adongCd 매칭 시도
        score_data = dong_scores.get(adm_cd)
        if not score_data:
            # 프리픽스 매칭 시도
            for key in dong_scores:
                if key.startswith(adm_cd[:5]) and key[:8] == adm_cd[:8]:
                    score_data = dong_scores[key]
                    break

        result.append(DongSummary(
            adong_cd=adm_cd,
            adong_nm=dong.get("adm_nm", ""),
            sido_cd=sido_code,
            signgu_nm=dong.get("sggnm", ""),
            total_stores=score_data["total_stores"] if score_data else 0,
            target_stores=score_data["target_stores"] if score_data else 0,
            density_score=score_data["score"] if score_data else 0,
        ))

    return result


@router.get("/regions/{sido_code}/analysis/{adong_cd}")
async def get_dong_analysis(
    request: Request,
    sido_code: str,
    adong_cd: str,
    business_type: str = Query(None, description="업종 코드"),
):
    """동 상세 분석 (비서울)"""
    if sido_code == "11":
        raise HTTPException(400, "서울은 /api/analysis/{code} 엔드포인트를 사용하세요")

    sido_info = SIDO_MAP.get(sido_code)
    if not sido_info:
        raise HTTPException(404, "해당 시도를 찾을 수 없습니다")

    semas_client = getattr(request.app.state, "semas_client", None)
    if not semas_client:
        raise HTTPException(503, "SEMAS API 클라이언트가 초기화되지 않았습니다")

    # 해당 동의 점포 조회
    stores = await semas_client.get_stores_in_dong(adong_cd)

    # 동 이름 찾기
    dong_list = _load_dong_list(sido_code)
    dong_name = adong_cd
    for d in dong_list:
        if d["adm_cd"] == adong_cd:
            dong_name = d["adm_nm"]
            break

    # 분석 실행
    analysis = compute_store_analysis(
        stores, dong_name, sido_info["name"], business_type
    )

    # 미진출 업종 추천
    missing_recs = recommend_missing_businesses_nationwide(stores)

    return NationwideAnalysisResponse(
        dong_code=adong_cd,
        dong_name=dong_name,
        region_name=sido_info["name"],
        data_source="SEMAS",
        total_score=analysis["total_score"],
        grade=analysis["grade"],
        breakdown=[ScoreBreakdownItem(**b) for b in analysis["breakdown"]],
        recommendation=analysis["recommendation"],
        store_summary=StoreSummary(
            total_stores=analysis["store_summary"]["total_stores"],
            category_distribution=[
                CategoryCount(**c) for c in analysis["store_summary"]["category_distribution"]
            ],
            top_businesses=analysis["store_summary"]["top_businesses"],
        ),
        missing_biz_recommendations=[BizRecommendation(**r) for r in missing_recs],
    )
