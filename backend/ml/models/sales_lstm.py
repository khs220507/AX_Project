"""매출 예측 LSTM 모델"""

import torch
import torch.nn as nn
from ml.config import NUM_TIMESERIES_FEATURES, LSTM_HIDDEN_DIM, LSTM_NUM_LAYERS, LSTM_DROPOUT, LSTM_OUTPUT_STEPS


class SalesLSTM(nn.Module):
    """
    다중 스텝 매출 예측 LSTM.
    Input:  (batch, seq_len, NUM_TIMESERIES_FEATURES)  -- 분기별 시계열
    Output: (batch, LSTM_OUTPUT_STEPS) -- 다음 4분기 예측 매출
    """

    def __init__(
        self,
        input_dim: int = NUM_TIMESERIES_FEATURES,
        hidden_dim: int = LSTM_HIDDEN_DIM,
        num_layers: int = LSTM_NUM_LAYERS,
        dropout: float = LSTM_DROPOUT,
        output_steps: int = LSTM_OUTPUT_STEPS,
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_dim, hidden_dim, num_layers,
            batch_first=True, dropout=dropout if num_layers > 1 else 0,
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, output_steps),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, input_dim)
        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]  # 마지막 타임스텝
        return self.fc(last_hidden)  # (batch, output_steps)
