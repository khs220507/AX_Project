"""모델별 성능 평가 지표 계산"""

import numpy as np
import torch
from torch.utils.data import DataLoader


def evaluate_regression(model, dataset, batch_size=128, collate_fn=None) -> dict:
    """회귀 모델 평가: MAE, RMSE, MAPE, R²"""
    model.eval()
    kwargs = {"batch_size": batch_size}
    if collate_fn:
        kwargs["collate_fn"] = collate_fn
    loader = DataLoader(dataset, **kwargs)

    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in loader:
            x, y = batch[0], batch[1]
            pred = model(x)
            all_preds.append(pred.numpy())
            all_targets.append(y.numpy())

    preds = np.concatenate(all_preds).flatten()
    targets = np.concatenate(all_targets).flatten()

    mae = float(np.mean(np.abs(preds - targets)))
    rmse = float(np.sqrt(np.mean((preds - targets) ** 2)))

    # MAPE (0 제외)
    nonzero = targets != 0
    if nonzero.sum() > 0:
        mape = float(np.mean(np.abs((targets[nonzero] - preds[nonzero]) / targets[nonzero])) * 100)
    else:
        mape = 0.0

    # R²
    ss_res = np.sum((targets - preds) ** 2)
    ss_tot = np.sum((targets - np.mean(targets)) ** 2)
    r2 = float(1 - ss_res / max(ss_tot, 1e-8))

    return {"mae": round(mae, 4), "rmse": round(rmse, 4), "mape": round(mape, 2), "r2": round(r2, 4)}


def evaluate_survival(model, dataset, batch_size=128) -> dict:
    """생존 예측 평가: AUC (근사), 평균 오차"""
    model.eval()
    loader = DataLoader(dataset, batch_size=batch_size)

    all_preds = []
    all_targets = []

    with torch.no_grad():
        for x, y in loader:
            pred = model(x)
            all_preds.append(pred.numpy())
            all_targets.append(y.numpy())

    preds = np.concatenate(all_preds)  # (N, 3)
    targets = np.concatenate(all_targets)  # (N, 3)

    labels = ["1yr", "3yr", "5yr"]
    result = {}
    for i, label in enumerate(labels):
        mae = float(np.mean(np.abs(preds[:, i] - targets[:, i])))
        result[f"mae_{label}"] = round(mae, 4)

        # 간이 AUC: 이진 분류 정확도 (0.5 기준)
        pred_binary = (preds[:, i] > 0.5).astype(int)
        target_binary = (targets[:, i] > 0.5).astype(int)
        acc = float(np.mean(pred_binary == target_binary))
        result[f"accuracy_{label}"] = round(acc, 4)

    return result


def evaluate_scoring(ensemble, features: np.ndarray, true_scores: np.ndarray) -> dict:
    """앙상블 점수 평가"""
    preds = ensemble.predict(features)
    mae = float(np.mean(np.abs(preds - true_scores)))
    rmse = float(np.sqrt(np.mean((preds - true_scores) ** 2)))
    ss_res = np.sum((true_scores - preds) ** 2)
    ss_tot = np.sum((true_scores - np.mean(true_scores)) ** 2)
    r2 = float(1 - ss_res / max(ss_tot, 1e-8))
    return {"mae": round(mae, 2), "rmse": round(rmse, 2), "r2": round(r2, 4)}


def evaluate_recommendation(model, dataset, batch_size=256) -> dict:
    """추천 모델 평가: 정확도, AUC 근사"""
    model.eval()
    loader = DataLoader(dataset, batch_size=batch_size)

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for area_feat, biz_idx, label in loader:
            pred = model(area_feat, biz_idx)
            all_preds.append(pred.numpy())
            all_labels.append(label.numpy())

    preds = np.concatenate(all_preds)
    labels = np.concatenate(all_labels)

    pred_binary = (preds > 0.5).astype(int)
    acc = float(np.mean(pred_binary == labels.astype(int)))
    precision = float(np.sum((pred_binary == 1) & (labels == 1)) / max(np.sum(pred_binary == 1), 1))
    recall = float(np.sum((pred_binary == 1) & (labels == 1)) / max(np.sum(labels == 1), 1))

    return {
        "accuracy": round(acc, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
    }
