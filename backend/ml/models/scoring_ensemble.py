"""상권 점수 앙상블 (XGBoost + PyTorch MLP)"""

import torch
import torch.nn as nn
import numpy as np
from ml.config import (
    NUM_STATIC_FEATURES, SCORING_MLP_HIDDEN_DIMS, SCORING_MLP_DROPOUT,
    SCORING_XGB_WEIGHT, SCORING_MLP_WEIGHT,
)


class ScoringMLP(nn.Module):
    """앙상블의 PyTorch MLP 컴포넌트"""

    def __init__(
        self,
        input_dim: int = NUM_STATIC_FEATURES,
        hidden_dims: list[int] | None = None,
        dropout: float = SCORING_MLP_DROPOUT,
    ):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = SCORING_MLP_HIDDEN_DIMS

        layers: list[nn.Module] = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h),
                nn.ReLU(),
                nn.Dropout(dropout),
            ])
            prev_dim = h
        layers.append(nn.Linear(prev_dim, 1))
        layers.append(nn.Sigmoid())  # 0~1, ×100으로 점수 변환

        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)  # (batch,)


class ScoringEnsemble:
    """XGBoost + MLP 앙상블 래퍼 (nn.Module 아님)"""

    def __init__(self):
        self.xgb_model = None  # xgboost.XGBRegressor
        self.mlp_model: ScoringMLP | None = None
        self.xgb_weight = SCORING_XGB_WEIGHT
        self.mlp_weight = SCORING_MLP_WEIGHT

    def predict(self, X: np.ndarray) -> np.ndarray:
        """앙상블 예측. X: (N, features) → (N,) 점수 0~100"""
        scores = np.zeros(len(X))

        if self.xgb_model is not None:
            xgb_pred = self.xgb_model.predict(X)
            xgb_pred = np.clip(xgb_pred, 0, 100)
            scores += self.xgb_weight * xgb_pred

        if self.mlp_model is not None:
            self.mlp_model.eval()
            with torch.no_grad():
                tensor_x = torch.tensor(X, dtype=torch.float32)
                mlp_pred = self.mlp_model(tensor_x).numpy() * 100
                mlp_pred = np.clip(mlp_pred, 0, 100)
            scores += self.mlp_weight * mlp_pred

        return np.clip(scores, 0, 100).astype(int)
