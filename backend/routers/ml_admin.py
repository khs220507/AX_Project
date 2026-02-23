"""ML 모델 관리자 API"""

import asyncio
from fastapi import APIRouter, Query, Request, HTTPException

router = APIRouter(prefix="/api/admin/ml", tags=["ML Admin"])


@router.get("/status")
async def ml_status(request: Request):
    """ML 모델 상태 조회"""
    model_manager = getattr(request.app.state, "model_manager", None)
    if not model_manager:
        return {"error": "ML module not initialized", "models": {}}
    return model_manager.get_status()


@router.get("/metrics")
async def ml_metrics(request: Request):
    """ML 모델 성능 지표 (정부 보고서용)"""
    model_manager = getattr(request.app.state, "model_manager", None)
    if not model_manager:
        return {}
    return model_manager.get_all_metrics()


@router.post("/train")
async def trigger_training(
    request: Request,
    model_name: str = Query(None, description="학습할 모델명 (없으면 전체)"),
):
    """모델 재학습 트리거 (백그라운드 실행)"""
    model_manager = getattr(request.app.state, "model_manager", None)
    if not model_manager:
        raise HTTPException(500, "ML module not initialized")

    if model_manager._training:
        return {"status": "already_training", "message": "학습이 이미 진행 중입니다"}

    client = request.app.state.seoul_client

    if model_name:
        valid_names = model_manager.MODEL_NAMES
        if model_name not in valid_names:
            raise HTTPException(400, f"Invalid model name. Choose from: {valid_names}")
        asyncio.create_task(model_manager.train_single(model_name, client))
        return {"status": "started", "model": model_name}
    else:
        asyncio.create_task(model_manager.train_all(client))
        return {"status": "started", "model": "all"}


@router.get("/metrics/export")
async def export_metrics(request: Request):
    """한국어 보고서용 성능 지표 내보내기"""
    model_manager = getattr(request.app.state, "model_manager", None)
    if not model_manager:
        return {"error": "ML module not initialized"}

    raw = model_manager.get_all_metrics()
    status = model_manager.get_status()

    report = {
        "제목": "AI 모델 성능 보고서",
        "모델_현황": {},
    }

    name_map = {
        "sales_lstm": "매출예측 LSTM",
        "survival_mlp": "생존예측 MLP",
        "scoring_ensemble": "상권점수 앙상블 (XGBoost+MLP)",
        "recommendation": "업종추천 임베딩모델",
    }

    for name, kr_name in name_map.items():
        metrics = raw.get(name, {})
        info = status.get("models", {}).get(name, {})

        entry = {
            "모델명": kr_name,
            "상태": "운영 중" if info.get("ready") else "미학습",
            "버전": info.get("version", 0),
            "학습일시": metrics.get("trained_at", ""),
            "학습샘플수": metrics.get("samples", 0),
            "학습시간_초": metrics.get("time_sec", 0),
        }

        # 모델별 핵심 지표
        if name == "sales_lstm":
            entry["MAE"] = metrics.get("mae", "")
            entry["RMSE"] = metrics.get("rmse", "")
            entry["MAPE(%)"] = metrics.get("mape", "")
            entry["R2"] = metrics.get("r2", "")
        elif name == "survival_mlp":
            entry["1년_정확도"] = metrics.get("accuracy_1yr", "")
            entry["3년_정확도"] = metrics.get("accuracy_3yr", "")
            entry["5년_정확도"] = metrics.get("accuracy_5yr", "")
        elif name == "scoring_ensemble":
            entry["MAE"] = metrics.get("mae", "")
            entry["R2"] = metrics.get("r2", "")
        elif name == "recommendation":
            entry["정확도"] = metrics.get("accuracy", "")
            entry["정밀도"] = metrics.get("precision", "")
            entry["재현율"] = metrics.get("recall", "")

        report["모델_현황"][kr_name] = entry

    return report
