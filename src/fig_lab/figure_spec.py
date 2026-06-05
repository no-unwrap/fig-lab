"""Figure specification types and JSON loader.

A figure spec is a serializable description of a single visualization: its data
source, chart kind, title, dimensions, and rendering backend.  Specs are loaded
from JSON files and fed to renderers without the renderer needing to know how
the upstream data was sourced.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fig_lab._parsing import load_json_object, string_or_none
from fig_lab._source_kinds import (
    PUBLISHED_RELEASE_BUNDLE,
    STANDALONE_METRIC_TABLE,
    SUPPORTED_DATASET_SOURCE_KINDS,
    SUPPORTED_EXPERIMENT_SOURCE_KINDS,
)

DATASET_CATEGORY_COUNTS = "dataset_category_counts"
EXPERIMENT_METRIC_BARS = "experiment_metric_bars"
SUPPORTED_FIGURE_KINDS = {
    DATASET_CATEGORY_COUNTS,
    EXPERIMENT_METRIC_BARS,
}
SUPPORTED_BACKENDS = {"matplotlib", "plotly"}
SUPPORTED_OUTPUT_FORMATS = {"png", "svg", "pdf", "html"}
SUPPORTED_BACKEND_OUTPUT_FORMATS = {
    "matplotlib": {"png", "svg", "pdf"},
    "plotly": {"html"},
}
DEFAULT_OUTPUT_FORMATS = {
    "matplotlib": "png",
    "plotly": "html",
}


@dataclass(frozen=True, slots=True)
class FigureSpecBase:
    """Common fields shared by every figure spec kind."""

    spec_id: str
    figure_kind: str
    title: str
    output_stem: str
    subtitle: str | None = None
    backend: str = "matplotlib"
    output_format: str = "png"
    width: float = 8.0
    height: float = 4.5

    def to_manifest_dict(self) -> dict[str, object]:
        """Serialize the spec fields for inclusion in an export manifest."""
        payload: dict[str, object] = {
            "spec_id": self.spec_id,
            "figure_kind": self.figure_kind,
            "title": self.title,
            "output_stem": self.output_stem,
            "backend": self.backend,
            "output_format": self.output_format,
            "width": self.width,
            "height": self.height,
        }
        if self.subtitle is not None:
            payload["subtitle"] = self.subtitle
        return payload


@dataclass(frozen=True, slots=True)
class DatasetCategoryCountFigureSpec(FigureSpecBase):
    """Spec for a horizontal bar chart of annotation counts per category."""

    dataset_source_kind: str = PUBLISHED_RELEASE_BUNDLE
    dataset_path: str = ""
    top_n: int | None = None
    task_type: str | None = None

    def to_manifest_dict(self) -> dict[str, object]:
        payload = FigureSpecBase.to_manifest_dict(self)
        payload["dataset_source_kind"] = self.dataset_source_kind
        payload["dataset_path"] = self.dataset_path
        if self.top_n is not None:
            payload["top_n"] = self.top_n
        if self.task_type is not None:
            payload["task_type"] = self.task_type
        return payload


@dataclass(frozen=True, slots=True)
class ExperimentMetricBarFigureSpec(FigureSpecBase):
    """Spec for a grouped horizontal bar chart of experiment metrics."""

    experiment_source_kind: str = STANDALONE_METRIC_TABLE
    experiment_path: str = ""
    metric: str = ""
    group_by: str = "model"
    aggregation: str = "mean"

    def to_manifest_dict(self) -> dict[str, object]:
        payload = FigureSpecBase.to_manifest_dict(self)
        payload["experiment_source_kind"] = self.experiment_source_kind
        payload["experiment_path"] = self.experiment_path
        payload["metric"] = self.metric
        payload["group_by"] = self.group_by
        payload["aggregation"] = self.aggregation
        return payload


FigureSpec = DatasetCategoryCountFigureSpec | ExperimentMetricBarFigureSpec


def load_figure_spec(spec_path: str | Path) -> FigureSpec:
    """Load and validate a JSON figure spec from *spec_path*."""
    resolved_spec_path = Path(spec_path).resolve()
    payload = load_json_object(resolved_spec_path)
    figure_kind = _require_string(payload, "figure_kind")
    if figure_kind not in SUPPORTED_FIGURE_KINDS:
        raise ValueError(f"unsupported figure_kind: {figure_kind}")

    backend = _validated_backend(payload.get("backend"))
    output_format = _validated_output_format(
        payload.get("output_format"),
        default=DEFAULT_OUTPUT_FORMATS[backend],
    )
    _validate_backend_output_format(backend, output_format)

    common_kwargs = {
        "spec_id": _require_string(payload, "spec_id"),
        "figure_kind": figure_kind,
        "title": _require_string(payload, "title"),
        "output_stem": string_or_none(payload.get("output_stem"))
        or _require_string(payload, "spec_id"),
        "subtitle": string_or_none(payload.get("subtitle")),
        "backend": backend,
        "output_format": output_format,
        "width": _validated_dimension(payload.get("width"), default=8.0),
        "height": _validated_dimension(payload.get("height"), default=4.5),
    }

    if figure_kind == DATASET_CATEGORY_COUNTS:
        bundle_dir = string_or_none(payload.get("bundle_dir"))
        explicit_dataset_source_kind = string_or_none(payload.get("dataset_source_kind"))
        if bundle_dir is not None and (
            explicit_dataset_source_kind is not None
            and explicit_dataset_source_kind != PUBLISHED_RELEASE_BUNDLE
        ):
            raise ValueError("bundle_dir may only be used with published_release_bundle")
        dataset_source_kind = _validated_dataset_source_kind(
            explicit_dataset_source_kind or PUBLISHED_RELEASE_BUNDLE
        )
        dataset_path = string_or_none(payload.get("dataset_path")) or bundle_dir
        if dataset_path is None:
            raise ValueError(
                "dataset_category_counts requires dataset_path or bundle_dir"
            )
        top_n = _optional_positive_int(payload.get("top_n"))
        return DatasetCategoryCountFigureSpec(
            dataset_source_kind=dataset_source_kind,
            dataset_path=dataset_path,
            top_n=top_n,
            task_type=string_or_none(payload.get("task_type")),
            **common_kwargs,
        )

    metric_table_path = string_or_none(payload.get("metric_table_path"))
    explicit_experiment_source_kind = string_or_none(payload.get("experiment_source_kind"))
    if metric_table_path is not None and (
        explicit_experiment_source_kind is not None
        and explicit_experiment_source_kind != STANDALONE_METRIC_TABLE
    ):
        raise ValueError("metric_table_path may only be used with standalone_metric_table")
    experiment_source_kind = _validated_experiment_source_kind(
        explicit_experiment_source_kind or STANDALONE_METRIC_TABLE
    )
    experiment_path = string_or_none(payload.get("experiment_path")) or metric_table_path
    if experiment_path is None:
        raise ValueError("experiment_metric_bars requires experiment_path or metric_table_path")
    return ExperimentMetricBarFigureSpec(
        experiment_source_kind=experiment_source_kind,
        experiment_path=experiment_path,
        metric=_require_string(payload, "metric"),
        group_by=_require_string(payload, "group_by", default="model"),
        aggregation=_require_string(payload, "aggregation", default="mean"),
        **common_kwargs,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _require_string(
    payload: dict[str, object],
    key: str,
    *,
    default: str | None = None,
) -> str:
    value = payload.get(key, default)
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise ValueError(f"figure spec field {key!r} must be a non-empty string")


def _validated_backend(value: object) -> str:
    backend = string_or_none(value) or "matplotlib"
    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"unsupported backend: {backend}")
    return backend


def _validated_output_format(value: object, *, default: str) -> str:
    output_format = string_or_none(value) or default
    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        raise ValueError(f"unsupported output_format: {output_format}")
    return output_format


def _validate_backend_output_format(backend: str, output_format: str) -> None:
    if output_format not in SUPPORTED_BACKEND_OUTPUT_FORMATS[backend]:
        raise ValueError(
            f"backend {backend!r} does not support output_format {output_format!r}"
        )


def _validated_dataset_source_kind(value: object) -> str:
    dataset_source_kind = string_or_none(value)
    if dataset_source_kind is None:
        raise ValueError("dataset_source_kind must be a non-empty string")
    normalized = dataset_source_kind.lower().replace("-", "_")
    if normalized not in SUPPORTED_DATASET_SOURCE_KINDS:
        raise ValueError(f"unsupported dataset_source_kind: {dataset_source_kind}")
    return normalized


def _validated_experiment_source_kind(value: object) -> str:
    experiment_source_kind = string_or_none(value)
    if experiment_source_kind is None:
        raise ValueError("experiment_source_kind must be a non-empty string")
    normalized = experiment_source_kind.lower().replace("-", "_")
    if normalized not in SUPPORTED_EXPERIMENT_SOURCE_KINDS:
        raise ValueError(f"unsupported experiment_source_kind: {experiment_source_kind}")
    return normalized


def _validated_dimension(value: object, *, default: float) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)) and float(value) > 0:
        return float(value)
    raise ValueError("figure dimensions must be positive numbers")


def _optional_positive_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int) and value > 0:
        return value
    raise ValueError("top_n must be a positive integer when provided")
