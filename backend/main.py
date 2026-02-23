import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from services.seoul_api import SeoulAPIClient
from services.semas_api import SEMASAPIClient
from routers import areas, analysis, prediction, trends, compare, regions, geojson, news, models, policy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 이벤트"""
    settings = get_settings()
    client = SeoulAPIClient(
        api_key=settings.SEOUL_API_KEY,
        cache_ttl=settings.CACHE_TTL,
    )
    app.state.seoul_client = client
    logger.info("Seoul API client initialized")

    # SEMAS API 클라이언트 (전국 점포 데이터)
    if settings.DATA_GO_KR_API_KEY:
        semas_client = SEMASAPIClient(
            base_url=settings.DATA_GO_KR_BASE_URL,
            api_key=settings.DATA_GO_KR_API_KEY,
            cache_ttl=settings.CACHE_TTL,
        )
        app.state.semas_client = semas_client
        logger.info("SEMAS API client initialized")
    else:
        app.state.semas_client = None
        logger.warning("DATA_GO_KR_API_KEY not set - nationwide features disabled")

    # 상권영역 목록 프리로드
    try:
        area_data = await client.get_areas()
        logger.info(f"Preloaded {len(area_data)} areas")
    except Exception as e:
        logger.warning(f"Failed to preload areas: {e}")

    yield

    # 종료 시 클라이언트 정리
    await client.close()
    if app.state.semas_client:
        await app.state.semas_client.close()
    logger.info("API clients closed")


app = FastAPI(
    title="소상공인 AI 상권분석 API",
    description="전국 상권 데이터 기반 상권입지분석 + 매출예측 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(areas.router)
app.include_router(analysis.router)
app.include_router(prediction.router)
app.include_router(trends.router)
app.include_router(compare.router)
app.include_router(regions.router)
app.include_router(geojson.router)
app.include_router(news.router)
app.include_router(models.router)
app.include_router(policy.router)


@app.get("/")
async def root():
    return {
        "title": "소상공인 AI 상권분석 API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "GET /api/areas",
            "GET /api/areas/{code}",
            "GET /api/analysis/{code}",
            "GET /api/models/{code}",
            "POST /api/predict",
            "GET /api/trends/{code}",
            "GET /api/compare?codes=A,B",
            "GET /api/business-types",
            "GET /api/regions",
            "GET /api/regions/{sido_code}/dongs",
            "GET /api/regions/{sido_code}/analysis/{adong_cd}",
            "GET /api/geojson/{sido_code}",
            "GET /api/news/trend?area_name=&business_type=",
            "GET /api/policies?business_type=",
        ],
    }
