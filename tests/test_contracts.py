"""Construction validation and summary tests for contract types."""

from __future__ import annotations

import pytest

from fig_lab.contracts import (
    DatasetView,
    FigureInputBundle,
    MetricRecord,
    MetricTable,
    VisualAsset,
    VisualCategory,
)


def test_figure_input_bundle_rejects_all_none_sources() -> None:
    with pytest.raises(ValueError, match="requires at least one of"):
        FigureInputBundle(
            bundle_id="bad",
            bundle_kind="dataset_view",
            source_artifacts=[],
            lineage=[],
            dataset_view=None,
            metric_table=None,
            metric_table_path=None,
        )


def test_figure_input_bundle_accepts_dataset_view_only() -> None:
    dataset_view = DatasetView(
        dataset_id="ds",
        dataset_version="1.0",
        source_kind="coco",
        task_types=["bbox"],
        assets=[
            VisualAsset(
                asset_id="1",
                file_name="img.jpg",
                image_path_or_uri=None,
                width=100,
                height=100,
            )
        ],
        categories=[VisualCategory(category_id="1", name="obj")],
        annotations=[],
    )
    bundle = FigureInputBundle(
        bundle_id="test",
        bundle_kind="dataset_view",
        source_artifacts=["a.json"],
        lineage=[],
        dataset_view=dataset_view,
    )

    assert bundle.dataset_view is not None


def test_figure_input_bundle_accepts_metric_table_path_only() -> None:
    bundle = FigureInputBundle(
        bundle_id="test",
        bundle_kind="metric_table",
        source_artifacts=["m.csv"],
        lineage=[],
        metric_table_path="/fake/metrics.csv",
    )

    assert bundle.metric_table_path is not None


def test_metric_table_summary_dict_returns_expected_keys() -> None:
    table = MetricTable(
        rows=[
            MetricRecord(
                metric="accuracy",
                value=0.91,
                source_artifact="results.json",
                source_run_id="run-001",
                model="vjepa",
            ),
            MetricRecord(
                metric="f1",
                value=0.88,
                source_artifact="results.json",
                source_run_id="run-001",
                model="vjepa",
            ),
        ],
    )

    summary = table.to_summary_dict()

    assert summary["row_count"] == 2
    assert sorted(summary["metrics"]) == ["accuracy", "f1"]
    assert summary["model_count"] == 1
    assert summary["source_run_count"] == 1
