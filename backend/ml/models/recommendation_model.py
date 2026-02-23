"""업종 추천 모델 (Embedding + MLP)"""

import torch
import torch.nn as nn
from ml.config import NUM_STATIC_FEATURES, NUM_BIZ_TYPES, REC_BIZ_EMBED_DIM, REC_HIDDEN_DIM, REC_DROPOUT


class BusinessRecommender(nn.Module):
    """
    상권-업종 적합도 예측.
    Input:  area_features (batch, NUM_STATIC_FEATURES) + biz_type_idx (batch,)
    Output: (batch, 1) -- 적합도 점수 (0~1)
    """

    def __init__(
        self,
        area_dim: int = NUM_STATIC_FEATURES,
        num_biz_types: int = NUM_BIZ_TYPES,
        biz_embed_dim: int = REC_BIZ_EMBED_DIM,
        hidden_dim: int = REC_HIDDEN_DIM,
        dropout: float = REC_DROPOUT,
    ):
        super().__init__()
        self.biz_embedding = nn.Embedding(num_biz_types, biz_embed_dim)
        self.fc = nn.Sequential(
            nn.Linear(area_dim + biz_embed_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

    def forward(self, area_features: torch.Tensor, biz_type_idx: torch.Tensor) -> torch.Tensor:
        biz_emb = self.biz_embedding(biz_type_idx)  # (batch, embed_dim)
        combined = torch.cat([area_features, biz_emb], dim=-1)
        return self.fc(combined).squeeze(-1)  # (batch,)
