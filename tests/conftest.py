"""Shared test fixtures for fig-lab.

Provides reusable helpers that build on-disk fixture data for release bundles,
repr-lab run directories, raw datasets, and metric tables.  Each builder writes
the minimum viable artifact set that satisfies the corresponding reader contract.
"""

from __future__ import annotations

import json
from pathlib import Path


def write_release_bundle(bundle_dir: Path) -> None:
    """Write a minimal published release bundle that satisfies the v1 contract."""
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "annotations.coco.json").write_text(
        json.dumps(
            {
                "images": [{"id": 1, "file_name": "scene.jpg", "width": 640, "height": 480}],
                "categories": [{"id": 7, "name": "signal-object", "supercategory": "object"}],
                "annotations": [
                    {
                        "id": 10,
                        "image_id": 1,
                        "category_id": 7,
                        "bbox": [1, 2, 3, 4],
                        "segmentation": [[1, 2, 4, 2, 4, 6, 1, 6]],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "assets.parquet").write_text("parquet-placeholder", encoding="utf-8")
    (bundle_dir / "categories.parquet").write_text("parquet-placeholder", encoding="utf-8")
    (bundle_dir / "release_manifest.json").write_text(
        json.dumps(
            {
                "contract_name": "published_artifact_bundle_contract",
                "contract_version": "1.0.0",
                "bundle_kind": "dataset_release_bundle",
                "release_id": "demo-release",
                "release_version": "1.0.0",
                "publisher_repo": "label-lab",
                "publisher_commit_sha": "abc123",
                "task_types": ["bbox", "instance_segmentation"],
                "artifact_paths": {
                    "annotations_coco": "annotations.coco.json",
                    "assets_table": "assets.parquet",
                    "categories_table": "categories.parquet",
                },
                "lineage": [],
                "dataset": {
                    "dataset_id": "demo-dataset",
                    "dataset_version": "1.0.0",
                },
            }
        ),
        encoding="utf-8",
    )


def write_repr_lab_run(run_dir: Path) -> None:
    """Write a minimal repr-lab run directory that satisfies the v1 contract."""
    artifacts_dir = run_dir / "artifacts"
    run_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / "probe_metrics.json").write_text(
        json.dumps({"metrics": {"top1_accuracy": 0.91}}),
        encoding="utf-8",
    )
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "contract_name": "repr_lab_run_directory_contract",
                "contract_version": "1.0.0",
                "run_directory_kind": "benchmark_run_directory",
                "producer_repo": "repr-lab",
                "name": "demo-run",
                "dataset": "demo-release",
                "model": "vjepa2",
                "seed": 7,
                "run_id": "run-001",
                "created_at": "2026-03-24T00:00:00+00:00",
                "tags": ["demo"],
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "benchmark_result.json").write_text(
        json.dumps(
            {
                "contract_name": "repr_lab_run_directory_contract",
                "contract_version": "1.0.0",
                "run_directory_kind": "benchmark_run_directory",
                "producer_repo": "repr-lab",
                "schema_version": "0.1.0",
                "run_id": "run-001",
                "release_id": "demo-release",
                "release_version": "1.0.0",
                "benchmark_task": "frozen-feature-localization-probe",
                "model_family": "vjepa2",
                "model_variant": "vjepa2-vitl16",
                "status": "succeeded",
                "started_at": "2026-03-24T00:00:00+00:00",
                "finished_at": "2026-03-24T00:01:00+00:00",
                "metrics": {
                    "top1_accuracy": 0.91,
                    "macro_f1": 0.88,
                },
                "artifact_paths": {
                    "probe_metrics": "artifacts/probe_metrics.json",
                },
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "result.json").write_text(
        json.dumps({"run_id": "run-001", "metrics": {"top1_accuracy": 0.91}}),
        encoding="utf-8",
    )


def write_raw_coco_dataset(dataset_path: Path) -> None:
    """Write a minimal COCO annotation file."""
    dataset_path.write_text(
        json.dumps(
            {
                "info": {"name": "demo-coco", "version": "2026.03"},
                "images": [
                    {"id": 1, "file_name": "scene.jpg", "width": 640, "height": 480}
                ],
                "categories": [
                    {"id": 7, "name": "signal-object", "supercategory": "object"}
                ],
                "annotations": [
                    {"id": 10, "image_id": 1, "category_id": 7, "bbox": [1, 2, 3, 4]}
                ],
            }
        ),
        encoding="utf-8",
    )


def write_raw_lvis_dataset(dataset_path: Path) -> None:
    """Write a minimal LVIS annotation file with frequency tiers."""
    dataset_path.write_text(
        json.dumps(
            {
                "info": {"name": "demo-lvis", "version": "1.0"},
                "images": [
                    {"id": 1, "file_name": "scene.jpg", "width": 800, "height": 600}
                ],
                "categories": [
                    {
                        "id": 9,
                        "name": "rare-object",
                        "supercategory": "object",
                        "frequency": "rare",
                    }
                ],
                "annotations": [
                    {
                        "id": 22,
                        "image_id": 1,
                        "category_id": 9,
                        "bbox": [10, 12, 20, 30],
                        "segmentation": [[10, 12, 30, 12, 30, 42, 10, 42]],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def write_pascal_voc_dataset(dataset_root: Path) -> None:
    """Write a minimal Pascal VOC dataset with Annotations and JPEGImages dirs."""
    annotations_dir = dataset_root / "Annotations"
    images_dir = dataset_root / "JPEGImages"
    annotations_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    (images_dir / "frame-001.jpg").write_text("image-placeholder", encoding="utf-8")
    (annotations_dir / "frame-001.xml").write_text(
        "\n".join(
            [
                "<annotation>",
                "  <folder>JPEGImages</folder>",
                "  <filename>frame-001.jpg</filename>",
                "  <size><width>1280</width><height>720</height><depth>3</depth></size>",
                "  <object>",
                "    <name>signal-object</name>",
                "    <pose>Unspecified</pose>",
                "    <truncated>0</truncated>",
                "    <difficult>0</difficult>",
                "    <bndbox>",
                "      <xmin>100</xmin>",
                "      <ymin>120</ymin>",
                "      <xmax>200</xmax>",
                "      <ymax>260</ymax>",
                "    </bndbox>",
                "  </object>",
                "</annotation>",
            ]
        ),
        encoding="utf-8",
    )


def write_metric_table(metric_table_path: Path) -> None:
    """Write a minimal CSV metric table with two models and two metrics."""
    metric_table_path.write_text(
        "\n".join(
            [
                "metric,value,model,source_artifact,source_run_id",
                "accuracy,0.91,vjepa,results.json,run-001",
                "accuracy,0.84,sam,results.json,run-002",
                "f1,0.72,vjepa,results.json,run-001",
            ]
        ),
        encoding="utf-8",
    )
