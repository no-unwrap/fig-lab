from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import write_release_bundle, write_repr_lab_run

from fig_lab.dataset_reader import load_dataset_bundle
from fig_lab.experiment_reader import load_repr_lab_run_directory
from fig_lab.metric_reader import load_metric_table_bundle
from fig_lab.release_reader import load_published_release_bundle


def test_release_reader_uses_shared_dataset_contract(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    write_release_bundle(bundle_dir)

    bundle = load_published_release_bundle(bundle_dir)

    assert bundle.dataset_view is not None
    assert bundle.dataset_view.source_kind == "published_release_bundle"
    assert bundle.dataset_view.annotations[0].task_type == "instance_segmentation"


def test_load_dataset_bundle_for_coco_normalizes_bbox_task(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(
        json.dumps(
            {
                "info": {"name": "demo-coco"},
                "images": [{"id": 1, "file_name": "scene.jpg", "width": 640, "height": 480}],
                "categories": [{"id": 7, "name": "signal-object"}],
                "annotations": [{"id": 10, "image_id": 1, "category_id": 7, "bbox": [1, 2, 3, 4]}],
            }
        ),
        encoding="utf-8",
    )

    bundle = load_dataset_bundle("coco", dataset_path)

    assert bundle.dataset_view is not None
    assert bundle.dataset_view.task_types == ["bbox"]
    assert bundle.dataset_view.annotations[0].bbox_xywh == [1.0, 2.0, 3.0, 4.0]


def test_load_repr_lab_run_directory_builds_metric_table(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-001"
    write_repr_lab_run(run_dir)

    bundle = load_repr_lab_run_directory(run_dir)

    assert bundle.metric_table is not None
    assert bundle.bundle_id == "run-001"
    assert len(bundle.metric_table.rows) == 2
    first_row = bundle.metric_table.rows[0]
    assert first_row.model == "vjepa2:vjepa2-vitl16"
    assert first_row.model_family == "vjepa2"
    assert first_row.model_variant == "vjepa2-vitl16"
    assert first_row.benchmark_task == "frozen-feature-localization-probe"
    assert first_row.status == "succeeded"


def test_load_repr_lab_run_directory_fails_on_unknown_contract(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-001"
    write_repr_lab_run(run_dir)
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["contract_name"] = "unexpected_contract"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported contract_name"):
        load_repr_lab_run_directory(run_dir)


def test_load_metric_table_bundle_preserves_optional_experiment_fields(tmp_path: Path) -> None:
    metric_table_path = tmp_path / "metrics.csv"
    metric_table_path.write_text(
        "\n".join(
            [
                (
                    "metric,value,model,model_family,model_variant,"
                    "benchmark_task,status,source_artifact,source_run_id"
                ),
                (
                    "top1_accuracy,0.91,vjepa2:vjepa2-vitl16,vjepa2,vjepa2-vitl16,"
                    "frozen-feature-localization-probe,succeeded,results.json,run-001"
                ),
            ]
        ),
        encoding="utf-8",
    )

    bundle = load_metric_table_bundle(metric_table_path)

    assert bundle.metric_table is not None
    row = bundle.metric_table.rows[0]
    assert row.model == "vjepa2:vjepa2-vitl16"
    assert row.model_family == "vjepa2"
    assert row.model_variant == "vjepa2-vitl16"
    assert row.benchmark_task == "frozen-feature-localization-probe"
    assert row.status == "succeeded"
