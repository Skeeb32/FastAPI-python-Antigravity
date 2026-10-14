"""
Pure Python dataset transformer and tabular data processing pipeline.

Features:
- Profiling of tabular dictionaries (missing values, types, cardinalities, basic stats)
- Imputation handling (mean, median, zero, row-drop)
- Feature scaling (Min-Max normalization, Standard Z-score scaling)
- Numeric clamping (winsorizing lower/upper boundaries)
- Clean, robust implementation using standard Python libraries
"""

import copy
import math
from typing import Any, Dict, List, Optional
from app.models.dataset import (
    ColumnProfile,
    ColumnTransformConfig,
    DatasetTransformRequest,
    DatasetTransformResponse,
    ImputationStrategy,
    ScalingMethod,
)


class DatasetTransformer:
    """
    Service responsible for cleaning, transforming, and profiling tabular records.
    """

    @staticmethod
    def _is_number(val: Any) -> bool:
        if val is None or isinstance(val, bool):
            return False
        return isinstance(val, (int, float)) and not math.isnan(val) and not math.isinf(val)

    @classmethod
    def profile_columns(cls, records: List[Dict[str, Any]]) -> List[ColumnProfile]:
        """
        Calculates column summary metadata across all records.
        """
        if not records:
            return []

        all_keys = set()
        for r in records:
            all_keys.update(r.keys())

        profiles: List[ColumnProfile] = []

        for col in sorted(all_keys):
            values = [r.get(col) for r in records]
            missing_count = sum(1 for v in values if v is None or (isinstance(v, float) and math.isnan(v)))
            valid_values = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]

            # Infer type
            numeric_vals = [float(v) for v in valid_values if cls._is_number(v)]
            is_numeric = len(numeric_vals) == len(valid_values) and len(numeric_vals) > 0

            data_type = "numeric" if is_numeric else "categorical"
            unique_count = len(set(valid_values)) if not is_numeric else len(set(numeric_vals))

            min_v = min(numeric_vals) if is_numeric else None
            max_v = max(numeric_vals) if is_numeric else None
            mean_v = round(sum(numeric_vals) / len(numeric_vals), 4) if is_numeric else None

            profiles.append(
                ColumnProfile(
                    column_name=col,
                    data_type=data_type,
                    count=len(values),
                    missing_count=missing_count,
                    unique_count=unique_count,
                    min_value=round(min_v, 4) if min_v is not None else None,
                    max_value=round(max_v, 4) if max_v is not None else None,
                    mean_value=mean_v,
                )
            )

        return profiles

    @classmethod
    def transform_dataset(cls, request: DatasetTransformRequest) -> DatasetTransformResponse:
        """
        Executes imputation, clamping, and scaling transformations on dataset records.
        """
        records = [copy.deepcopy(r) for r in request.records]
        config_map: Dict[str, ColumnTransformConfig] = {c.column_name: c for c in request.columns_to_transform}

        # Step 1: Imputation
        for col_name, cfg in config_map.items():
            col_numbers = [float(r[col_name]) for r in records if col_name in r and cls._is_number(r[col_name])]

            if not col_numbers:
                continue

            replacement_val = 0.0
            if cfg.imputation == ImputationStrategy.MEAN:
                replacement_val = sum(col_numbers) / len(col_numbers)
            elif cfg.imputation == ImputationStrategy.MEDIAN:
                sorted_nums = sorted(col_numbers)
                mid = len(sorted_nums) // 2
                replacement_val = sorted_nums[mid] if len(sorted_nums) % 2 != 0 else (sorted_nums[mid - 1] + sorted_nums[mid]) / 2.0
            elif cfg.imputation == ImputationStrategy.ZERO:
                replacement_val = 0.0

            if cfg.imputation == ImputationStrategy.DROP:
                records = [r for r in records if col_name in r and cls._is_number(r[col_name])]
            else:
                for r in records:
                    if col_name not in r or not cls._is_number(r[col_name]):
                        r[col_name] = round(replacement_val, 4)

        # Step 2: Clamping & Scaling
        for col_name, cfg in config_map.items():
            col_numbers = [float(r[col_name]) for r in records if col_name in r and cls._is_number(r[col_name])]
            if not col_numbers:
                continue

            # Clamping
            for r in records:
                if col_name in r and cls._is_number(r[col_name]):
                    val = float(r[col_name])
                    if cfg.clamp_min is not None and val < cfg.clamp_min:
                        val = cfg.clamp_min
                    if cfg.clamp_max is not None and val > cfg.clamp_max:
                        val = cfg.clamp_max
                    r[col_name] = val

            # Recalculate post-clamping stats for scaling
            col_numbers = [float(r[col_name]) for r in records if col_name in r and cls._is_number(r[col_name])]
            min_v = min(col_numbers)
            max_v = max(col_numbers)
            mean_v = sum(col_numbers) / len(col_numbers)
            variance = sum((x - mean_v) ** 2 for x in col_numbers) / max(1, len(col_numbers) - 1)
            std_dev = math.sqrt(variance)

            # Apply scaling
            if cfg.scaling == ScalingMethod.MIN_MAX and (max_v - min_v) > 1e-9:
                span = max_v - min_v
                for r in records:
                    if col_name in r and cls._is_number(r[col_name]):
                        r[col_name] = round((float(r[col_name]) - min_v) / span, 4)

            elif cfg.scaling == ScalingMethod.STANDARD and std_dev > 1e-9:
                for r in records:
                    if col_name in r and cls._is_number(r[col_name]):
                        r[col_name] = round((float(r[col_name]) - mean_v) / std_dev, 4)

        # Step 3: Column Filtering (if drop_unspecified_columns is enabled)
        if request.drop_unspecified_columns:
            keep_cols = set(config_map.keys()) | {"id", "_id", "name"}
            filtered_records = []
            for r in records:
                filtered_records.append({k: v for k, v in r.items() if k in keep_cols})
            records = filtered_records

        # Calculate final profiles
        profiles = cls.profile_columns(records)

        return DatasetTransformResponse(
            dataset_name=request.dataset_name,
            original_row_count=len(request.records),
            transformed_row_count=len(records),
            column_profiles=profiles,
            transformed_records=records,
        )
