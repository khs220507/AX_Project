"""모델 버전 관리: 저장/로드/롤백"""

import json
import shutil
import logging
from pathlib import Path
from datetime import datetime

from ml.config import MAX_VERSIONS_KEEP

logger = logging.getLogger(__name__)


class ModelVersionManager:
    """모델별 버전 관리"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _model_dir(self, model_name: str) -> Path:
        return self.base_dir / model_name

    def _meta_path(self, model_name: str) -> Path:
        return self._model_dir(model_name) / "metadata.json"

    def _load_meta(self, model_name: str) -> dict:
        meta_path = self._meta_path(model_name)
        if meta_path.exists():
            return json.loads(meta_path.read_text(encoding="utf-8"))
        return {"latest_version": 0, "versions": []}

    def _save_meta(self, model_name: str, meta: dict):
        meta_path = self._meta_path(model_name)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def next_version_dir(self, model_name: str) -> tuple[Path, int]:
        """다음 버전 디렉토리 생성 및 반환"""
        meta = self._load_meta(model_name)
        new_version = meta["latest_version"] + 1
        version_dir = self._model_dir(model_name) / f"v{new_version}"
        version_dir.mkdir(parents=True, exist_ok=True)
        return version_dir, new_version

    def commit_version(self, model_name: str, version: int, metrics: dict):
        """새 버전 확정 및 메타데이터 업데이트"""
        meta = self._load_meta(model_name)
        meta["latest_version"] = version
        if version not in meta["versions"]:
            meta["versions"].append(version)

        # 메트릭 저장
        version_dir = self._model_dir(model_name) / f"v{version}"
        metrics_path = version_dir / "metrics.json"
        metrics["trained_at"] = datetime.now().isoformat()
        metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

        self._save_meta(model_name, meta)
        self._cleanup_old_versions(model_name)
        logger.info(f"Model '{model_name}' v{version} committed. Metrics: {metrics}")

    def latest_version_dir(self, model_name: str) -> Path | None:
        """최신 버전 디렉토리 반환"""
        meta = self._load_meta(model_name)
        if meta["latest_version"] == 0:
            return None
        return self._model_dir(model_name) / f"v{meta['latest_version']}"

    def latest_version(self, model_name: str) -> int:
        return self._load_meta(model_name)["latest_version"]

    def get_metrics(self, model_name: str, version: int | None = None) -> dict:
        """지정 버전(또는 최신)의 메트릭 반환"""
        if version is None:
            version = self._load_meta(model_name)["latest_version"]
        metrics_path = self._model_dir(model_name) / f"v{version}" / "metrics.json"
        if metrics_path.exists():
            return json.loads(metrics_path.read_text(encoding="utf-8"))
        return {}

    def get_all_metrics(self) -> dict:
        """모든 모델의 최신 메트릭 반환"""
        result = {}
        if not self.base_dir.exists():
            return result
        for model_dir in self.base_dir.iterdir():
            if model_dir.is_dir() and (model_dir / "metadata.json").exists():
                name = model_dir.name
                meta = self._load_meta(name)
                metrics = self.get_metrics(name)
                result[name] = {
                    "version": meta["latest_version"],
                    "metrics": metrics,
                }
        return result

    def _cleanup_old_versions(self, model_name: str):
        """오래된 버전 삭제 (최근 N개만 유지)"""
        meta = self._load_meta(model_name)
        versions = sorted(meta["versions"])
        while len(versions) > MAX_VERSIONS_KEEP:
            old_v = versions.pop(0)
            old_dir = self._model_dir(model_name) / f"v{old_v}"
            if old_dir.exists():
                shutil.rmtree(old_dir)
                logger.info(f"Removed old model version: {model_name}/v{old_v}")
        meta["versions"] = versions
        self._save_meta(model_name, meta)
