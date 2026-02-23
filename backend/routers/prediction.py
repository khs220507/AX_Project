from fastapi import APIRouter, HTTPException, Request
from models.schemas import (
    PredictRequest, PredictResponse, QuarterlyPrediction, PredictFactor,
)
from services.prediction_service import predict_sales
from services.data_processor import get_biz_name, RECENT_QUARTERS

router = APIRouter(prefix="/api")


@router.post("/predict", response_model=PredictResponse)
async def predict(request: Request, body: PredictRequest):
    """매출 예측"""
    client = request.app.state.seoul_client

    # 여러 분기 매출 데이터 수집
    all_sales = []
    for yyqu in RECENT_QUARTERS:
        rows = await client.get_sales(yyqu)
        # STDR_YYQU_CD → STDR_YR_CD, STDR_QU_CD 분리 추가
        for r in rows:
            yyqu_val = str(r.get("STDR_YYQU_CD", ""))
            if len(yyqu_val) == 5:
                r["STDR_YR_CD"] = yyqu_val[:4]
                r["STDR_QU_CD"] = yyqu_val[4]
            all_sales.append(r)

    if not all_sales:
        raise HTTPException(503, "매출 데이터를 가져올 수 없습니다")

    biz_name = get_biz_name(body.business_type)
    result = predict_sales(all_sales, body.area_code, body.business_type)

    return PredictResponse(
        area_code=result["area_code"],
        business_type=biz_name,
        current_quarter_sales=result["current_quarter_sales"],
        predicted_next_quarter=result["predicted_next_quarter"],
        growth_rate=result["growth_rate"],
        confidence_lower=result["confidence_lower"],
        confidence_upper=result["confidence_upper"],
        quarterly_predictions=[
            QuarterlyPrediction(**p) for p in result["quarterly_predictions"]
        ],
        factors=[PredictFactor(**f) for f in result["factors"]],
    )
