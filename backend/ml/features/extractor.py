"""Seoul API 원시 데이터 → 피처 배열 변환"""

import numpy as np
import logging
from ml.config import (
    POP_TIME_FIELDS, POP_DAY_FIELDS, POP_AGE_FIELDS,
    SALES_TIME_FIELDS, SALES_DAY_FIELDS, SALES_AGE_FIELDS,
    STORE_FIELDS, FACILITY_FIELDS,
    NUM_TIMESERIES_FEATURES, NUM_STATIC_FEATURES,
)

logger = logging.getLogger(__name__)


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "" or value == "null":
            return default
        return int(float(str(value)))
    except (ValueError, TypeError):
        return default


def _extract_fields(rows: list[dict], fields: list[str]) -> list[float]:
    """여러 행에서 필드별 합계를 추출"""
    result = []
    for field in fields:
        total = sum(_safe_int(r.get(field)) for r in rows)
        result.append(float(total))
    return result


class FeatureExtractor:
    """Seoul API 데이터에서 ML 피처를 추출"""

    def extract_single(
        self,
        area_code: str,
        pop_data: list[dict],
        sales_data: list[dict],
        store_data: list[dict],
        facility_data: list[dict] | None = None,
        year: int = 2025,
        quarter: int = 3,
        lat: float = 37.5665,
        lng: float = 126.978,
    ) -> np.ndarray:
        """단일 상권의 정적 피처 벡터 추출. shape: (NUM_STATIC_FEATURES,)"""
        area_pop = [r for r in pop_data if str(r.get("TRDAR_CD")) == area_code]
        area_sales = [r for r in sales_data if str(r.get("TRDAR_CD")) == area_code]
        area_stores = [r for r in store_data if str(r.get("TRDAR_CD")) == area_code]

        # 시계열 피처 (40)
        features = []
        features.extend(_extract_fields(area_pop, POP_TIME_FIELDS))
        features.extend(_extract_fields(area_pop, POP_DAY_FIELDS))
        features.extend(_extract_fields(area_pop, POP_AGE_FIELDS))
        features.extend(_extract_fields(area_sales, SALES_TIME_FIELDS))
        features.extend(_extract_fields(area_sales, SALES_DAY_FIELDS))
        features.extend(_extract_fields(area_sales, SALES_AGE_FIELDS))
        features.extend(_extract_fields(area_stores, STORE_FIELDS))

        # 집객시설 피처 (13)
        if facility_data:
            area_fac = [r for r in facility_data if str(r.get("TRDAR_CD")) == area_code]
            features.extend(_extract_fields(area_fac, FACILITY_FIELDS))
        else:
            features.extend([0.0] * len(FACILITY_FIELDS))

        # 시간/위치 피처 (4)
        features.extend([float(year), float(quarter), lat, lng])

        return np.array(features, dtype=np.float32)

    def extract_timeseries(
        self,
        area_code: str,
        pop_by_quarter: dict[str, list[dict]],
        sales_by_quarter: dict[str, list[dict]],
        store_by_quarter: dict[str, list[dict]],
        quarters: list[str],
    ) -> np.ndarray:
        """시계열 피처 추출 (LSTM용). shape: (num_quarters, NUM_TIMESERIES_FEATURES)"""
        series = []
        for yyqu in quarters:
            pop_data = pop_by_quarter.get(yyqu, [])
            sales_data = sales_by_quarter.get(yyqu, [])
            store_data = store_by_quarter.get(yyqu, [])

            area_pop = [r for r in pop_data if str(r.get("TRDAR_CD")) == area_code]
            area_sales = [r for r in sales_data if str(r.get("TRDAR_CD")) == area_code]
            area_stores = [r for r in store_data if str(r.get("TRDAR_CD")) == area_code]

            step = []
            step.extend(_extract_fields(area_pop, POP_TIME_FIELDS))
            step.extend(_extract_fields(area_pop, POP_DAY_FIELDS))
            step.extend(_extract_fields(area_pop, POP_AGE_FIELDS))
            step.extend(_extract_fields(area_sales, SALES_TIME_FIELDS))
            step.extend(_extract_fields(area_sales, SALES_DAY_FIELDS))
            step.extend(_extract_fields(area_sales, SALES_AGE_FIELDS))
            step.extend(_extract_fields(area_stores, STORE_FIELDS))

            series.append(step)

        return np.array(series, dtype=np.float32)

    def extract_target_sales(
        self,
        area_code: str,
        biz_code: str,
        sales_by_quarter: dict[str, list[dict]],
        quarters: list[str],
    ) -> list[float]:
        """분기별 총 매출액 추출 (예측 타겟)"""
        targets = []
        for yyqu in quarters:
            rows = sales_by_quarter.get(yyqu, [])
            area_biz = [
                r for r in rows
                if str(r.get("TRDAR_CD")) == area_code
                and str(r.get("SVC_INDUTY_CD")) == biz_code
            ]
            total = sum(_safe_int(r.get("THSMON_SELNG_AMT")) for r in area_biz)
            targets.append(float(total))
        return targets

    def extract_batch_static(
        self,
        area_codes: list[str],
        pop_data: list[dict],
        sales_data: list[dict],
        store_data: list[dict],
        facility_data: list[dict] | None = None,
        year: int = 2025,
        quarter: int = 3,
        lat_lng_map: dict[str, tuple[float, float]] | None = None,
    ) -> np.ndarray:
        """배치 정적 피처 추출. shape: (N, NUM_STATIC_FEATURES)"""
        all_features = []
        for code in area_codes:
            lat, lng = (37.5665, 126.978)
            if lat_lng_map and code in lat_lng_map:
                lat, lng = lat_lng_map[code]
            feat = self.extract_single(
                code, pop_data, sales_data, store_data,
                facility_data, year, quarter, lat, lng,
            )
            all_features.append(feat)
        return np.stack(all_features) if all_features else np.zeros((0, NUM_STATIC_FEATURES), dtype=np.float32)
