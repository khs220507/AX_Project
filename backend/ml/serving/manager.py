"""ModelManager: 모델 학습, 로드, 추론, fallback 관리"""

import asyncio
import logging
import time
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from collections import defaultdict

from ml.config import (
    MODEL_DIR, NUM_STATIC_FEATURES, NUM_TIMESERIES_FEATURES,
    BIZ_CODE_TO_IDX, NUM_BIZ_TYPES, LSTM_MIN_QUARTERS, LSTM_OUTPUT_STEPS,
    LSTM_EPOCHS, LSTM_BATCH_SIZE, LSTM_LR,
    SURVIVAL_EPOCHS, SURVIVAL_BATCH_SIZE, SURVIVAL_LR,
    SCORING_MLP_EPOCHS, SCORING_MLP_LR,
    REC_EPOCHS, REC_BATCH_SIZE, REC_LR,
)
from ml.features.extractor import FeatureExtractor, _safe_int
from ml.features.scaler import FeatureScaler
from ml.models.sales_lstm import SalesLSTM
from ml.models.survival_mlp import SurvivalMLP
from ml.models.scoring_ensemble import ScoringEnsemble, ScoringMLP
from ml.models.recommendation_model import BusinessRecommender
from ml.training.dataset import (
    SalesDataset, SurvivalDataset, ScoringDataset, RecommendationDataset,
    collate_sales,
)
from ml.training.trainer import Trainer
from ml.training.evaluator import (
    evaluate_regression, evaluate_survival, evaluate_scoring, evaluate_recommendation,
)
from ml.storage.versioning import ModelVersionManager

# data_processor에서 RECENT_QUARTERS 가져오기 방지 (순환 import)
RECENT_QUARTERS = ["20234", "20241", "20242", "20243", "20244", "20251", "20252", "20253"]

logger = logging.getLogger(__name__)


class ModelManager:
    """ML 모델 라이프사이클 관리자"""

    MODEL_NAMES = ["sales_lstm", "survival_mlp", "scoring_ensemble", "recommendation"]

    def __init__(self, model_dir: Path | None = None):
        self.model_dir = model_dir or MODEL_DIR
        self.version_mgr = ModelVersionManager(self.model_dir)
        self.extractor = FeatureExtractor()

        # 모델 인스턴스
        self._models: dict[str, nn.Module | ScoringEnsemble] = {}
        self._scalers: dict[str, FeatureScaler] = {}
        self._ready: dict[str, bool] = {name: False for name in self.MODEL_NAMES}
        self._training = False

    def is_ready(self, model_name: str) -> bool:
        return self._ready.get(model_name, False)

    def needs_training(self) -> bool:
        return not all(self._ready.values())

    # ── 모델 로드 ─────────────────────────────────────────

    def load_all(self) -> int:
        """디스크에서 학습된 모델 로드. 로드된 모델 수 반환."""
        loaded = 0
        for name in self.MODEL_NAMES:
            try:
                if self._load_model(name):
                    loaded += 1
            except Exception as e:
                logger.warning(f"Failed to load model '{name}': {e}")
        return loaded

    def _load_model(self, name: str) -> bool:
        version_dir = self.version_mgr.latest_version_dir(name)
        if version_dir is None:
            return False

        scaler_path = version_dir / "scaler.pkl"
        if scaler_path.exists():
            self._scalers[name] = FeatureScaler().load(scaler_path)

        if name == "sales_lstm":
            model = SalesLSTM()
            model.load_state_dict(torch.load(version_dir / "model.pt", weights_only=True))
            model.eval()
            self._models[name] = model
        elif name == "survival_mlp":
            model = SurvivalMLP()
            model.load_state_dict(torch.load(version_dir / "model.pt", weights_only=True))
            model.eval()
            self._models[name] = model
        elif name == "scoring_ensemble":
            ensemble = ScoringEnsemble()
            mlp = ScoringMLP()
            mlp.load_state_dict(torch.load(version_dir / "mlp_model.pt", weights_only=True))
            mlp.eval()
            ensemble.mlp_model = mlp
            try:
                import joblib
                xgb_path = version_dir / "xgb_model.pkl"
                if xgb_path.exists():
                    ensemble.xgb_model = joblib.load(xgb_path)
            except Exception:
                pass
            self._models[name] = ensemble
        elif name == "recommendation":
            model = BusinessRecommender()
            model.load_state_dict(torch.load(version_dir / "model.pt", weights_only=True))
            model.eval()
            self._models[name] = model

        self._ready[name] = True
        v = self.version_mgr.latest_version(name)
        logger.info(f"Loaded model '{name}' v{v}")
        return True

    # ── 추론 ──────────────────────────────────────────────

    def predict_sales_lstm(
        self,
        area_code: str,
        biz_code: str,
        pop_by_q: dict[str, list[dict]],
        sales_by_q: dict[str, list[dict]],
        store_by_q: dict[str, list[dict]],
    ) -> dict | None:
        """LSTM 매출 예측. 실패 시 None 반환."""
        if not self.is_ready("sales_lstm"):
            return None

        model = self._models["sales_lstm"]
        scaler = self._scalers.get("sales_lstm")

        # 피처 추출
        features = self.extractor.extract_timeseries(
            area_code, pop_by_q, sales_by_q, store_by_q, RECENT_QUARTERS,
        )
        if features.shape[0] < LSTM_MIN_QUARTERS:
            return None

        # 타겟 매출 (역변환용)
        sales_targets = self.extractor.extract_target_sales(
            area_code, biz_code, sales_by_q, RECENT_QUARTERS,
        )
        current_sales = sales_targets[-1] if sales_targets else 0

        # 스케일링
        if scaler and scaler.is_fitted:
            features = scaler.transform(features)

        # 추론
        model.eval()
        with torch.no_grad():
            x = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
            pred = model(x).squeeze(0).numpy()

        # MC Dropout 신뢰 구간 (10회 추론)
        model.train()  # dropout 활성화
        mc_preds = []
        with torch.no_grad():
            for _ in range(10):
                p = model(x).squeeze(0).numpy()
                mc_preds.append(p)
        model.eval()

        mc_preds = np.array(mc_preds)
        mc_std = mc_preds.std(axis=0)

        # 예측값 복원 (로그 변환 사용 안 함 — 스케일러로 처리)
        predictions = []
        last_q = int(RECENT_QUARTERS[-1][4])
        last_year = int(RECENT_QUARTERS[-1][:4])

        for step in range(LSTM_OUTPUT_STEPS):
            next_q = (last_q + step) % 4 + 1
            next_year = last_year + (last_q + step) // 4
            predicted = max(0, int(pred[step]))
            lower = max(0, int(pred[step] - 1.96 * mc_std[step]))
            upper = max(0, int(pred[step] + 1.96 * mc_std[step]))

            predictions.append({
                "quarter": f"{next_year}-Q{next_q}",
                "predicted": predicted,
                "lower": lower,
                "upper": upper,
            })

        next_pred = predictions[0]["predicted"] if predictions else 0
        growth_rate = ((next_pred - current_sales) / max(current_sales, 1)) * 100

        return {
            "area_code": area_code,
            "business_type": biz_code,
            "current_quarter_sales": int(current_sales),
            "predicted_next_quarter": next_pred,
            "growth_rate": round(growth_rate, 1),
            "confidence_lower": predictions[0]["lower"] if predictions else 0,
            "confidence_upper": predictions[0]["upper"] if predictions else 0,
            "quarterly_predictions": predictions,
            "factors": [{"name": "LSTM 딥러닝 예측", "impact": f"{growth_rate:+.1f}%"}],
            "historical": [
                {"quarter": RECENT_QUARTERS[i], "sales": int(s)}
                for i, s in enumerate(sales_targets) if s > 0
            ],
        }

    def predict_survival(
        self,
        area_code: str,
        pop_data: list[dict],
        sales_data: list[dict],
        store_data: list[dict],
        facility_data: list[dict] | None = None,
    ) -> dict | None:
        """MLP 생존 예측. 실패 시 None 반환."""
        if not self.is_ready("survival_mlp"):
            return None

        model = self._models["survival_mlp"]
        scaler = self._scalers.get("survival_mlp")

        features = self.extractor.extract_single(
            area_code, pop_data, sales_data, store_data, facility_data,
        )
        if scaler and scaler.is_fitted:
            features = scaler.transform(features.reshape(1, -1)).flatten()

        model.eval()
        with torch.no_grad():
            x = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
            pred = model(x).squeeze(0).numpy()

        return {
            "survival_1yr": round(float(pred[0]) * 100, 1),
            "survival_3yr": round(float(pred[1]) * 100, 1),
            "survival_5yr": round(float(pred[2]) * 100, 1),
        }

    def predict_score(
        self,
        area_code: str,
        pop_data: list[dict],
        sales_data: list[dict],
        store_data: list[dict],
        facility_data: list[dict] | None = None,
    ) -> int | None:
        """앙상블 상권 점수. 실패 시 None."""
        if not self.is_ready("scoring_ensemble"):
            return None

        ensemble = self._models["scoring_ensemble"]
        scaler = self._scalers.get("scoring_ensemble")

        features = self.extractor.extract_single(
            area_code, pop_data, sales_data, store_data, facility_data,
        )
        if scaler and scaler.is_fitted:
            features = scaler.transform(features.reshape(1, -1))
        else:
            features = features.reshape(1, -1)

        scores = ensemble.predict(features)
        return int(scores[0])

    def recommend_businesses(
        self,
        area_code: str,
        pop_data: list[dict],
        sales_data: list[dict],
        store_data: list[dict],
        facility_data: list[dict] | None = None,
    ) -> list[dict] | None:
        """업종 추천. 실패 시 None."""
        if not self.is_ready("recommendation"):
            return None

        model = self._models["recommendation"]
        scaler = self._scalers.get("recommendation")

        area_feat = self.extractor.extract_single(
            area_code, pop_data, sales_data, store_data, facility_data,
        )
        if scaler and scaler.is_fitted:
            area_feat = scaler.transform(area_feat.reshape(1, -1)).flatten()

        model.eval()
        idx_to_code = {v: k for k, v in BIZ_CODE_TO_IDX.items()}
        results = []

        with torch.no_grad():
            area_tensor = torch.tensor(area_feat, dtype=torch.float32).unsqueeze(0).expand(NUM_BIZ_TYPES, -1)
            biz_tensor = torch.arange(NUM_BIZ_TYPES, dtype=torch.long)
            scores = model(area_tensor, biz_tensor).numpy()

        for i in range(NUM_BIZ_TYPES):
            results.append({
                "biz_code": idx_to_code[i],
                "score": round(float(scores[i]) * 100, 1),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    # ── 학습 ──────────────────────────────────────────────

    async def train_all(self, seoul_client):
        """전체 모델 학습 (백그라운드)"""
        if self._training:
            logger.warning("Training already in progress")
            return
        self._training = True
        try:
            logger.info("=== ML Model Training Started ===")

            # 데이터 수집
            data = await self._collect_data(seoul_client)

            # 순차 학습 (CPU이므로 병렬 불필요)
            await asyncio.to_thread(self._train_survival, data)
            await asyncio.to_thread(self._train_sales_lstm, data)
            await asyncio.to_thread(self._train_scoring, data)
            await asyncio.to_thread(self._train_recommendation, data)

            logger.info("=== ML Model Training Completed ===")
        except Exception as e:
            logger.error(f"Training failed: {e}", exc_info=True)
        finally:
            self._training = False

    async def train_single(self, model_name: str, seoul_client):
        """단일 모델 학습"""
        data = await self._collect_data(seoul_client)
        train_fn = {
            "sales_lstm": self._train_sales_lstm,
            "survival_mlp": self._train_survival,
            "scoring_ensemble": self._train_scoring,
            "recommendation": self._train_recommendation,
        }.get(model_name)
        if train_fn:
            await asyncio.to_thread(train_fn, data)

    async def _collect_data(self, seoul_client) -> dict:
        """Seoul API 캐시에서 학습 데이터 수집"""
        pop_by_q = {}
        sales_by_q = {}
        store_by_q = {}

        for yyqu in RECENT_QUARTERS:
            pop_by_q[yyqu] = await seoul_client.get_floating_pop(yyqu)
            sales_by_q[yyqu] = await seoul_client.get_sales(yyqu)
            store_by_q[yyqu] = await seoul_client.get_stores(yyqu)

        facility_data = await seoul_client.get_facilities(RECENT_QUARTERS[-1])

        # 상권 코드 목록
        area_codes = set()
        for rows in pop_by_q.values():
            for r in rows:
                area_codes.add(str(r.get("TRDAR_CD", "")))
        area_codes.discard("")

        return {
            "pop_by_q": pop_by_q,
            "sales_by_q": sales_by_q,
            "store_by_q": store_by_q,
            "facility_data": facility_data,
            "area_codes": sorted(area_codes),
        }

    def _train_survival(self, data: dict):
        """생존 예측 MLP 학습"""
        logger.info("Training survival_mlp...")

        pop = data["pop_by_q"].get(RECENT_QUARTERS[-1], [])
        sales = data["sales_by_q"].get(RECENT_QUARTERS[-1], [])
        stores = data["store_by_q"].get(RECENT_QUARTERS[-1], [])
        facility = data.get("facility_data")
        area_codes = data["area_codes"]

        # 피처 추출
        features_list = []
        labels_list = []

        for code in area_codes:
            feat = self.extractor.extract_single(code, pop, sales, stores, facility)
            features_list.append(feat)

            # 라벨: 폐업률 기반 생존 확률 계산
            area_stores_rows = [r for r in stores if str(r.get("TRDAR_CD")) == code]
            total_st = sum(_safe_int(r.get("STOR_CO")) for r in area_stores_rows)
            closes = sum(_safe_int(r.get("CLSBIZ_STOR_CO")) for r in area_stores_rows)
            close_rate = closes / max(total_st, 1)
            quarterly_survival = 1 - close_rate

            s1 = max(0, min(1, quarterly_survival ** 4))
            s3 = max(0, min(1, quarterly_survival ** 12))
            s5 = max(0, min(1, quarterly_survival ** 20))
            labels_list.append([s1, s3, s5])

        if len(features_list) < 10:
            logger.warning("Not enough data for survival training")
            return

        X = np.stack(features_list)
        y = np.array(labels_list, dtype=np.float32)

        scaler = FeatureScaler().fit(X)
        X_scaled = scaler.transform(X)

        dataset = SurvivalDataset(X_scaled, y)
        model = SurvivalMLP()
        trainer = Trainer(model, lr=SURVIVAL_LR)
        history = trainer.train(
            dataset, epochs=SURVIVAL_EPOCHS,
            batch_size=SURVIVAL_BATCH_SIZE,
            loss_fn=nn.BCELoss(),
        )

        # 저장
        version_dir, version = self.version_mgr.next_version_dir("survival_mlp")
        torch.save(model.state_dict(), version_dir / "model.pt")
        scaler.save(version_dir / "scaler.pkl")

        metrics = evaluate_survival(model, dataset)
        metrics["samples"] = len(dataset)
        metrics.update(history)
        self.version_mgr.commit_version("survival_mlp", version, metrics)

        self._models["survival_mlp"] = model
        self._scalers["survival_mlp"] = scaler
        self._ready["survival_mlp"] = True

    def _train_sales_lstm(self, data: dict):
        """매출 예측 LSTM 학습"""
        logger.info("Training sales_lstm...")

        area_codes = data["area_codes"]
        pop_by_q = data["pop_by_q"]
        sales_by_q = data["sales_by_q"]
        store_by_q = data["store_by_q"]

        sequences = []
        targets = []

        for code in area_codes:
            ts = self.extractor.extract_timeseries(
                code, pop_by_q, sales_by_q, store_by_q, RECENT_QUARTERS,
            )
            if ts.shape[0] < LSTM_MIN_QUARTERS + 1:
                continue

            # 입력: 처음 ~ 마지막-1, 타겟: 마지막 4분기 매출
            input_seq = ts[:-1]  # (seq_len-1, features)

            # 타겟: 마지막 4분기의 총매출 (단순화)
            target_vals = []
            for q_idx in range(max(0, ts.shape[0] - LSTM_OUTPUT_STEPS), ts.shape[0]):
                # 총매출 = SALES_TIME_FIELDS 합계 (인덱스 18~23)
                total_sales = ts[q_idx, 18:24].sum()
                target_vals.append(float(total_sales))

            while len(target_vals) < LSTM_OUTPUT_STEPS:
                target_vals.append(target_vals[-1] if target_vals else 0)

            sequences.append(input_seq)
            targets.append(np.array(target_vals[:LSTM_OUTPUT_STEPS], dtype=np.float32))

        if len(sequences) < 10:
            logger.warning("Not enough data for LSTM training")
            return

        # 스케일링 (시계열 전체를 하나의 행렬로)
        all_flat = np.vstack(sequences)
        scaler = FeatureScaler().fit(all_flat)
        scaled_seqs = [scaler.transform(s) for s in sequences]

        dataset = SalesDataset(scaled_seqs, targets)
        model = SalesLSTM()
        trainer = Trainer(model, lr=LSTM_LR)
        history = trainer.train(
            dataset, epochs=LSTM_EPOCHS,
            batch_size=LSTM_BATCH_SIZE,
            loss_fn=nn.MSELoss(),
            collate_fn=collate_sales,
        )

        version_dir, version = self.version_mgr.next_version_dir("sales_lstm")
        torch.save(model.state_dict(), version_dir / "model.pt")
        scaler.save(version_dir / "scaler.pkl")

        metrics = evaluate_regression(model, dataset, collate_fn=collate_sales)
        metrics["samples"] = len(dataset)
        metrics.update(history)
        self.version_mgr.commit_version("sales_lstm", version, metrics)

        self._models["sales_lstm"] = model
        self._scalers["sales_lstm"] = scaler
        self._ready["sales_lstm"] = True

    def _train_scoring(self, data: dict):
        """상권 점수 앙상블 학습"""
        logger.info("Training scoring_ensemble...")

        # 기존 룰 기반 점수를 라벨로 사용
        from services.data_processor import compute_location_score

        pop = data["pop_by_q"].get(RECENT_QUARTERS[-1], [])
        sales = data["sales_by_q"].get(RECENT_QUARTERS[-1], [])
        stores = data["store_by_q"].get(RECENT_QUARTERS[-1], [])
        facility = data.get("facility_data")
        area_codes = data["area_codes"]

        features_list = []
        scores_list = []

        for code in area_codes:
            feat = self.extractor.extract_single(code, pop, sales, stores, facility)
            features_list.append(feat)

            score_result = compute_location_score(code, sales, pop, stores, facility_data=facility)
            scores_list.append(score_result["total_score"])

        if len(features_list) < 10:
            logger.warning("Not enough data for scoring training")
            return

        X = np.stack(features_list)
        y = np.array(scores_list, dtype=np.float32)

        scaler = FeatureScaler().fit(X)
        X_scaled = scaler.transform(X)

        # XGBoost
        ensemble = ScoringEnsemble()
        try:
            from xgboost import XGBRegressor
            xgb = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
            xgb.fit(X_scaled, y)
            ensemble.xgb_model = xgb
        except ImportError:
            logger.warning("XGBoost not installed, using MLP only")
            ensemble.xgb_weight = 0.0
            ensemble.mlp_weight = 1.0

        # MLP
        mlp_dataset = ScoringDataset(X_scaled, y)
        mlp = ScoringMLP()
        trainer = Trainer(mlp, lr=SCORING_MLP_LR)
        history = trainer.train(mlp_dataset, epochs=SCORING_MLP_EPOCHS, batch_size=128, loss_fn=nn.MSELoss())
        ensemble.mlp_model = mlp

        # 저장
        version_dir, version = self.version_mgr.next_version_dir("scoring_ensemble")
        torch.save(mlp.state_dict(), version_dir / "mlp_model.pt")
        scaler.save(version_dir / "scaler.pkl")

        if ensemble.xgb_model is not None:
            import joblib
            joblib.dump(ensemble.xgb_model, version_dir / "xgb_model.pkl")

        metrics = evaluate_scoring(ensemble, X_scaled, y)
        metrics["samples"] = len(X)
        metrics.update(history)
        self.version_mgr.commit_version("scoring_ensemble", version, metrics)

        self._models["scoring_ensemble"] = ensemble
        self._scalers["scoring_ensemble"] = scaler
        self._ready["scoring_ensemble"] = True

    def _train_recommendation(self, data: dict):
        """업종 추천 모델 학습"""
        logger.info("Training recommendation...")

        pop = data["pop_by_q"].get(RECENT_QUARTERS[-1], [])
        sales = data["sales_by_q"].get(RECENT_QUARTERS[-1], [])
        stores = data["store_by_q"].get(RECENT_QUARTERS[-1], [])
        facility = data.get("facility_data")
        area_codes = data["area_codes"]

        area_features = []
        biz_indices = []
        labels = []

        for code in area_codes:
            feat = self.extractor.extract_single(code, pop, sales, stores, facility)

            area_stores = [r for r in stores if str(r.get("TRDAR_CD")) == code]
            area_sales = [r for r in sales if str(r.get("TRDAR_CD")) == code]

            for biz_code, biz_idx in BIZ_CODE_TO_IDX.items():
                biz_store_count = sum(
                    _safe_int(r.get("STOR_CO"))
                    for r in area_stores if str(r.get("SVC_INDUTY_CD")) == biz_code
                )
                biz_sales = sum(
                    _safe_int(r.get("THSMON_SELNG_AMT"))
                    for r in area_sales if str(r.get("SVC_INDUTY_CD")) == biz_code
                )

                # 라벨: 점포가 있고 매출이 중앙값 이상이면 1
                label = 1.0 if biz_store_count > 0 and biz_sales > 0 else 0.0

                area_features.append(feat)
                biz_indices.append(biz_idx)
                labels.append(label)

        if len(labels) < 100:
            logger.warning("Not enough data for recommendation training")
            return

        X = np.stack(area_features)
        biz_arr = np.array(biz_indices, dtype=np.int64)
        y = np.array(labels, dtype=np.float32)

        scaler = FeatureScaler().fit(X)
        X_scaled = scaler.transform(X)

        dataset = RecommendationDataset(X_scaled, biz_arr, y)
        model = BusinessRecommender()
        trainer = Trainer(model, lr=REC_LR)
        history = trainer.train(
            dataset, epochs=REC_EPOCHS,
            batch_size=REC_BATCH_SIZE,
            loss_fn=nn.BCELoss(),
        )

        version_dir, version = self.version_mgr.next_version_dir("recommendation")
        torch.save(model.state_dict(), version_dir / "model.pt")
        scaler.save(version_dir / "scaler.pkl")

        metrics = evaluate_recommendation(model, dataset)
        metrics["samples"] = len(dataset)
        metrics.update(history)
        self.version_mgr.commit_version("recommendation", version, metrics)

        self._models["recommendation"] = model
        self._scalers["recommendation"] = scaler
        self._ready["recommendation"] = True

    # ── 상태 조회 ─────────────────────────────────────────

    def get_status(self) -> dict:
        result = {"training_in_progress": self._training, "models": {}}
        for name in self.MODEL_NAMES:
            v = self.version_mgr.latest_version(name)
            metrics = self.version_mgr.get_metrics(name) if v > 0 else {}
            result["models"][name] = {
                "ready": self._ready.get(name, False),
                "version": v,
                "trained_at": metrics.get("trained_at", ""),
                "samples": metrics.get("samples", 0),
            }
        return result

    def get_all_metrics(self) -> dict:
        result = {}
        for name in self.MODEL_NAMES:
            metrics = self.version_mgr.get_metrics(name)
            result[name] = metrics
        return result
