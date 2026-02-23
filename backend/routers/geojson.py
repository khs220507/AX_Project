import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

GEOJSON_DIR = Path(__file__).parent.parent / "data" / "geojson"

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


@router.get("/geojson/{sido_code}")
async def get_geojson(sido_code: str):
    """시도별 GeoJSON 서빙"""
    filename = SIDO_GEOJSON_MAP.get(sido_code)
    if not filename:
        raise HTTPException(404, f"시도 코드 '{sido_code}'를 찾을 수 없습니다")

    filepath = GEOJSON_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, f"GeoJSON 파일이 없습니다: {filename}")

    return FileResponse(
        filepath,
        media_type="application/geo+json",
        headers={"Cache-Control": "public, max-age=86400"},
    )
