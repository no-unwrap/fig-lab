"""Canonical figure-facing data contracts.

Every reader normalizes its source-specific format into these frozen dataclasses
before figure specs or renderers see the data.  The contracts are intentionally
source-agnostic: a ``DatasetView`` built from COCO, LVIS, Pascal VOC, or a
published release bundle all look the same to downstream consumers.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class VisualAsset:
    """A single image or scene in a dataset."""

    asset_id: str
    file_name: str
    image_path_or_uri: str | None
    width: int
    height: int
    split: str | None = None
    source_asset_id: str | None = None
    thumbnail_path_or_uri: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VisualCategory:
    """An annotation category (e.g. object class) in a dataset."""

    category_id: str
    name: str
    supercategory: str | None = None
    frequency_tier: str | None = None
    color_hint: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VisualAnnotation:
    """A single annotation instance tied to an asset and category."""

    annotation_id: str
    asset_id: str
    category_id: str | None
    category_name: str | None
    task_type: str
    bbox_xywh: list[float] | None = None
    polygons: list[list[float]] = field(default_factory=list)
    rle: dict[str, object] | None = None
    keypoints_xyv: list[float] | None = None
    area: float | None = None
    iscrowd: bool | None = None
    score: float | None = None
    source_annotation_id: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VisualSceneRating:
    """A scene-level qualitative rating for a single asset."""

    asset_id: str
    scale_name: str
    value: int | float | str
    annotator_id: str | None = None
    session_id: str | None = None
    cohort: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DatasetView:
    """Normalized view of a dataset ready for figure-facing consumption."""

    dataset_id: str
    dataset_version: str | None
    source_kind: str
    task_types: list[str]
    assets: list[VisualAsset]
    categories: list[VisualCategory]
    annotations: list[VisualAnnotation]
    scene_ratings: list[VisualSceneRating] = field(default_factory=list)
    lineage: list[dict[str, object]] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MetricRecord:
    """A single metric measurement from an experiment run."""

    metric: str
    value: float
    source_artifact: str
    source_run_id: str
    dataset_id: str | None = None
    split: str | None = None
    cohort: str | None = None
    model: str | None = None
    model_family: str | None = None
    model_variant: str | None = None
    run_id: str | None = None
    group: str | None = None
    step: str | None = None
    benchmark_task: str | None = None
    status: str | None = None
    stderr: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    n: int | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MetricTable:
    """A collection of metric records with shared lineage."""

    rows: list[MetricRecord]
    lineage: list[dict[str, object]] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    def to_summary_dict(self) -> dict[str, object]:
        """Return a compact summary suitable for CLI output or manifest embedding."""
        metrics = sorted({row.metric for row in self.rows})
        models = sorted({row.model for row in self.rows if row.model})
        runs = sorted({row.source_run_id for row in self.rows})
        return {
            "row_count": len(self.rows),
            "metrics": metrics,
            "model_count": len(models),
            "source_run_count": len(runs),
        }


@dataclass(frozen=True, slots=True)
class FigureInputBundle:
    """Top-level input container that pairs a dataset view or metric table with provenance."""

    bundle_id: str
    bundle_kind: str
    source_artifacts: list[str]
    lineage: list[dict[str, object]]
    dataset_view: DatasetView | None = None
    metric_table: MetricTable | None = None
    metric_table_path: str | None = None
    embedding_table_path: str | None = None
    qualitative_sample_ids: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (
            self.dataset_view is None
            and self.metric_table is None
            and self.metric_table_path is None
        ):
            raise ValueError(
                "FigureInputBundle requires at least one of: "
                "dataset_view, metric_table, metric_table_path"
            )

    def to_summary_dict(self) -> dict[str, object]:
        """Return a compact summary suitable for CLI output or manifest embedding."""
        payload: dict[str, object] = {
            "bundle_id": self.bundle_id,
            "bundle_kind": self.bundle_kind,
            "source_artifacts": self.source_artifacts,
            "metadata": self.metadata,
        }
        dataset_view = self.dataset_view
        if dataset_view is not None:
            payload["dataset_view"] = {
                "dataset_id": dataset_view.dataset_id,
                "dataset_version": dataset_view.dataset_version,
                "source_kind": dataset_view.source_kind,
                "task_types": dataset_view.task_types,
                "asset_count": len(dataset_view.assets),
                "category_count": len(dataset_view.categories),
                "annotation_count": len(dataset_view.annotations),
            }
        if self.metric_table is not None:
            payload["metric_table"] = self.metric_table.to_summary_dict()
        elif self.metric_table_path is not None:
            payload["metric_table"] = {
                "row_count": None,
                "source_path": self.metric_table_path,
            }
        return payload
