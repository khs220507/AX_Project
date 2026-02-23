"""PyTorch Dataset 클래스 4종"""

import numpy as np
import torch
from torch.utils.data import Dataset


class SalesDataset(Dataset):
    """LSTM 매출 예측용 시계열 데이터셋"""

    def __init__(self, sequences: list[np.ndarray], targets: list[np.ndarray]):
        """
        sequences: list of (seq_len, features) arrays
        targets: list of (output_steps,) arrays
        """
        self.sequences = [torch.tensor(s, dtype=torch.float32) for s in sequences]
        self.targets = [torch.tensor(t, dtype=torch.float32) for t in targets]

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


class SurvivalDataset(Dataset):
    """MLP 생존 예측용 정적 피처 데이터셋"""

    def __init__(self, features: np.ndarray, labels: np.ndarray):
        """
        features: (N, num_features)
        labels: (N, 3) -- 1yr/3yr/5yr 생존 확률
        """
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


class ScoringDataset(Dataset):
    """상권 점수 예측용 데이터셋"""

    def __init__(self, features: np.ndarray, scores: np.ndarray):
        """
        features: (N, num_features)
        scores: (N,) -- 0~100 점수 (0~1로 정규화하여 사용)
        """
        self.features = torch.tensor(features, dtype=torch.float32)
        self.scores = torch.tensor(scores / 100.0, dtype=torch.float32)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, idx):
        return self.features[idx], self.scores[idx]


class RecommendationDataset(Dataset):
    """업종 추천용 데이터셋"""

    def __init__(
        self,
        area_features: np.ndarray,
        biz_indices: np.ndarray,
        labels: np.ndarray,
    ):
        """
        area_features: (N, num_features)
        biz_indices: (N,) -- 업종 인덱스 0~14
        labels: (N,) -- 적합도 0 or 1
        """
        self.area_features = torch.tensor(area_features, dtype=torch.float32)
        self.biz_indices = torch.tensor(biz_indices, dtype=torch.long)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.area_features[idx], self.biz_indices[idx], self.labels[idx]


def collate_sales(batch):
    """가변 길이 시퀀스를 패딩하여 배치 생성"""
    sequences, targets = zip(*batch)
    max_len = max(s.shape[0] for s in sequences)
    feat_dim = sequences[0].shape[1]

    padded = torch.zeros(len(sequences), max_len, feat_dim)
    for i, s in enumerate(sequences):
        padded[i, :s.shape[0], :] = s

    targets = torch.stack(targets)
    return padded, targets
