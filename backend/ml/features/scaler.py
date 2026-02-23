"""피처 스케일링 래퍼 (저장/로드 지원)"""

import numpy as np
import joblib
from pathlib import Path


class FeatureScaler:
    """StandardScaler 래퍼: fit → transform → save/load"""

    def __init__(self):
        self.mean_: np.ndarray | None = None
        self.std_: np.ndarray | None = None
        self._fitted = False

    def fit(self, X: np.ndarray) -> "FeatureScaler":
        self.mean_ = X.mean(axis=0)
        self.std_ = X.std(axis=0)
        self.std_[self.std_ < 1e-8] = 1.0  # 상수 피처 보호
        self._fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Scaler not fitted yet")
        return (X - self.mean_) / self.std_

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        self.fit(X)
        return self.transform(X)

    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("Scaler not fitted yet")
        return X * self.std_ + self.mean_

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"mean": self.mean_, "std": self.std_}, path)

    def load(self, path: Path) -> "FeatureScaler":
        data = joblib.load(path)
        self.mean_ = data["mean"]
        self.std_ = data["std"]
        self._fitted = True
        return self
