"""통합 학습 루프: Early stopping, LR scheduler"""

import logging
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from ml.config import EARLY_STOPPING_PATIENCE, VAL_SPLIT

logger = logging.getLogger(__name__)


class Trainer:
    """PyTorch 모델 범용 학습기"""

    def __init__(
        self,
        model: nn.Module,
        lr: float = 0.001,
        patience: int = EARLY_STOPPING_PATIENCE,
    ):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", factor=0.5, patience=5,
        )
        self.patience = patience

    def train(
        self,
        dataset,
        epochs: int = 100,
        batch_size: int = 64,
        loss_fn: nn.Module | None = None,
        collate_fn=None,
    ) -> dict:
        """
        학습 실행. 자동으로 train/val 분할.
        Returns: {"train_losses": [...], "val_losses": [...], "best_epoch": int, "time_sec": float}
        """
        if loss_fn is None:
            loss_fn = nn.MSELoss()

        # Train/Val 분할
        val_size = max(1, int(len(dataset) * VAL_SPLIT))
        train_size = len(dataset) - val_size
        train_ds, val_ds = random_split(dataset, [train_size, val_size])

        loader_kwargs = {"batch_size": batch_size, "shuffle": True}
        if collate_fn:
            loader_kwargs["collate_fn"] = collate_fn
        train_loader = DataLoader(train_ds, **loader_kwargs)

        val_kwargs = {"batch_size": batch_size}
        if collate_fn:
            val_kwargs["collate_fn"] = collate_fn
        val_loader = DataLoader(val_ds, **val_kwargs)

        best_val_loss = float("inf")
        best_state = None
        best_epoch = 0
        no_improve = 0

        train_losses = []
        val_losses = []
        start_time = time.time()

        for epoch in range(epochs):
            # ── Train ──
            self.model.train()
            epoch_loss = 0.0
            n_batches = 0
            for batch in train_loader:
                self.optimizer.zero_grad()
                loss = self._compute_loss(batch, loss_fn)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                self.optimizer.step()
                epoch_loss += loss.item()
                n_batches += 1

            avg_train = epoch_loss / max(n_batches, 1)
            train_losses.append(avg_train)

            # ── Validation ──
            self.model.eval()
            val_loss = 0.0
            n_val = 0
            with torch.no_grad():
                for batch in val_loader:
                    loss = self._compute_loss(batch, loss_fn)
                    val_loss += loss.item()
                    n_val += 1

            avg_val = val_loss / max(n_val, 1)
            val_losses.append(avg_val)
            self.scheduler.step(avg_val)

            # ── Early stopping ──
            if avg_val < best_val_loss:
                best_val_loss = avg_val
                best_state = {k: v.clone() for k, v in self.model.state_dict().items()}
                best_epoch = epoch
                no_improve = 0
            else:
                no_improve += 1

            if (epoch + 1) % 20 == 0:
                logger.info(
                    f"Epoch {epoch+1}/{epochs} - "
                    f"train_loss: {avg_train:.6f}, val_loss: {avg_val:.6f}"
                )

            if no_improve >= self.patience:
                logger.info(f"Early stopping at epoch {epoch+1} (best: {best_epoch+1})")
                break

        # 최적 모델 복원
        if best_state:
            self.model.load_state_dict(best_state)

        elapsed = time.time() - start_time
        logger.info(f"Training done in {elapsed:.1f}s. Best epoch: {best_epoch+1}, val_loss: {best_val_loss:.6f}")

        return {
            "train_losses": train_losses,
            "val_losses": val_losses,
            "best_epoch": best_epoch + 1,
            "best_val_loss": float(best_val_loss),
            "time_sec": round(elapsed, 1),
        }

    def _compute_loss(self, batch, loss_fn):
        """배치 형태에 따라 loss 계산"""
        if len(batch) == 2:
            x, y = batch
            pred = self.model(x)
            return loss_fn(pred, y)
        elif len(batch) == 3:
            # RecommendationDataset: (area_features, biz_idx, label)
            area_feat, biz_idx, label = batch
            pred = self.model(area_feat, biz_idx)
            return loss_fn(pred, label)
        else:
            raise ValueError(f"Unexpected batch length: {len(batch)}")
