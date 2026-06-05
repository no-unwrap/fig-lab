"""Standalone metric table reader for CSV and JSON sources.

Normalizes flat metric files into ``MetricRecord`` rows wrapped in a
``FigureInputBundle``.  Required columns are ``metric``, ``value``,
``source_artifact``, and ``source_run_id``; additional faceting and uncertainty
columns are preserved when present.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from fig_lab._parsing import string_or_none
from fig_lab.contracts import FigureInputBundle, MetricRecord, MetricTable

REQUIRED_METRIC_COLUMNS = (
    "metric",
    "value",
    "source_artifact",
    "source_run_id",
)


def load_metric_table_bundle(metric_table_path: str | Path) -> FigureInputBundle:
    """Load a standalone metric table (CSV or JSON) into a normalized bundle."""
    resolved_metric_table_path = Path(metric_table_path).resolve()
    rows = _load_rows(resolved_metric_table_path)
    metric_rows = [
        _build_metric_record(
            row,
            row_index=index,
            fallback_source_artifact=str(resolved_metric_table_path),
        )
        for index, row in enumerate(rows, start=1)
    ]
    metric_table = MetricTable(
        rows=metric_rows,
        lineage=[
            {
                "source_kind": "standalone_metric_table",
                "source_artifact": str(resolved_metric_table_path),
            }
        ],
        metadata={
            "source_format": resolved_metric_table_path.suffix.lstrip("."),
        },
    )
    return FigureInputBundle(
        bundle_id=resolved_metric_table_path.stem,
        bundle_kind="metric_table",
        source_artifacts=[str(resolved_metric_table_path)],
        lineage=metric_table.lineage,
        metric_table=metric_table,
        metric_table_path=str(resolved_metric_table_path),
        metadata=metric_table.metadata,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_rows(path: Path) -> list[dict[str, object]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _load_csv_rows(path)
    if suffix == ".json":
        return _load_json_rows(path)
    raise ValueError(f"unsupported metric table format: {path.suffix or '<none>'}")


def _load_csv_rows(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"metric table is missing a header row: {path}")
        rows = [dict(row) for row in reader]
    return rows


def _load_json_rows(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("rows")
    if not isinstance(payload, list):
        raise ValueError(f"metric table JSON must be a list or a dict with 'rows': {path}")
    rows: list[dict[str, object]] = []
    for row in payload:
        if not isinstance(row, dict):
            raise ValueError(f"metric table rows must be JSON objects: {path}")
        rows.append(dict(row))
    return rows


def _build_metric_record(
    row: dict[str, object],
    *,
    row_index: int,
    fallback_source_artifact: str,
) -> MetricRecord:
    metric = _require_string(row, "metric", row_index=row_index)
    value = _require_float(row, "value", row_index=row_index)
    source_artifact = (
        string_or_none(row.get("source_artifact")) or fallback_source_artifact
    )
    source_run_id = _require_string(row, "source_run_id", row_index=row_index)
    return MetricRecord(
        metric=metric,
        value=value,
        source_artifact=source_artifact,
        source_run_id=source_run_id,
        dataset_id=string_or_none(row.get("dataset_id")),
        split=string_or_none(row.get("split")),
        cohort=string_or_none(row.get("cohort")),
        model=string_or_none(row.get("model")),
        model_family=string_or_none(row.get("model_family")),
        model_variant=string_or_none(row.get("model_variant")),
        run_id=string_or_none(row.get("run_id")),
        group=string_or_none(row.get("group")),
        step=string_or_none(row.get("step")),
        benchmark_task=string_or_none(row.get("benchmark_task")),
        status=string_or_none(row.get("status")),
        stderr=_optional_float(row.get("stderr")),
        ci_low=_optional_float(row.get("ci_low")),
        ci_high=_optional_float(row.get("ci_high")),
        n=_optional_int(row.get("n")),
    )


def _require_string(row: dict[str, object], key: str, *, row_index: int) -> str:
    value = string_or_none(row.get(key))
    if value is None:
        raise ValueError(f"metric table row {row_index} is missing required field {key!r}")
    return value


def _require_float(row: dict[str, object], key: str, *, row_index: int) -> float:
    value = _optional_float(row.get(key))
    if value is None:
        raise ValueError(f"metric table row {row_index} has non-numeric {key!r}")
    return value


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        return float(value)
    return None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        return int(value)
    return None
