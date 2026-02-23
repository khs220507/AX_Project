"""생존 예측 MLP 분류기"""

import torch
import torch.nn as nn
from ml.config import NUM_STATIC_FEATURES, SURVIVAL_HIDDEN_DIMS, SURVIVAL_DROPOUT


class SurvivalMLP(nn.Module):
    """
    다중 출력 생존 확률 예측.
    Input:  (batch, NUM_STATIC_FEATURES)
    Output: (batch, 3) -- 1년/3년/5년 생존 확률 (0~1)
    """

    def __init__(
        self,
        input_dim: int = NUM_STATIC_FEATURES,
        hidden_dims: list[int] | None = None,
        dropout: float = SURVIVAL_DROPOUT,
    ):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = SURVIVAL_HIDDEN_DIMS

        layers: list[nn.Module] = []
        prev_dim = input_dim
        for h in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h),
                nn.BatchNorm1d(h),
                nn.ReLU(),
                nn.Dropout(dropout),
            ])
            prev_dim = h
        layers.append(nn.Linear(prev_dim, 3))
        layers.append(nn.Sigmoid())

        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)  # (batch, 3)
