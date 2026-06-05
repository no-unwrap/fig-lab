from __future__ import annotations

import json
from pathlib import Path

from conftest import (
    write_metric_table,
    write_pascal_voc_dataset,
    write_raw_coco_dataset,
    write_raw_lvis_dataset,
    write_release_bundle,
    write_repr_lab_run,
)

import fig_lab.smoke as smoke_module
from fig_lab.main import main
from fig_lab.release_reader import load_published_release_bundle


def test_main_without_args_prints_help(capsys) -> None:
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "usage:" in captured.out.lower()


def test_main_version_flag_prints_version(capsys) -> None:
    exit_code = main(["--version"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "fig-lab 0.1.0" in captured.out


def test_smoke_subcommand_delegates(monkeypatch) -> None:
    calls: list[str] = []

    def fake_main() -> int:
        calls.append("smoke")
        return 7

    monkeypatch.setattr(smoke_module, "main", fake_main)

    exit_code = main(["smoke"])

    assert exit_code == 7
    assert calls == ["smoke"]


def test_release_reader_builds_dataset_view(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    write_release_bundle(bundle_dir)

    bundle = load_published_release_bundle(bundle_dir)

    assert bundle.bundle_id == "demo-release"
    assert bundle.dataset_view is not None
    assert bundle.dataset_view.dataset_id == "demo-dataset"
    assert len(bundle.dataset_view.assets) == 1
    assert bundle.dataset_view.annotations[0].task_type == "instance_segmentation"
    assert bundle.dataset_view.source_kind == "published_release_bundle"


def test_inspect_release_cli_prints_summary(tmp_path: Path, capsys) -> None:
    bundle_dir = tmp_path / "bundle"
    write_release_bundle(bundle_dir)

    exit_code = main(["inspect-release", "--bundle-dir", str(bundle_dir)])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["bundle_id"] == "demo-release"
    assert payload["dataset_view"]["asset_count"] == 1


def test_inspect_dataset_cli_prints_coco_summary(tmp_path: Path, capsys) -> None:
    dataset_path = tmp_path / "dataset.coco.json"
    write_raw_coco_dataset(dataset_path)

    exit_code = main(
        [
            "inspect-dataset",
            "--source-kind",
            "coco",
            "--source-path",
            str(dataset_path),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["bundle_id"] == "demo-coco"
    assert payload["dataset_view"]["source_kind"] == "coco"
    assert payload["dataset_view"]["annotation_count"] == 1


def test_inspect_experiment_cli_prints_repr_lab_summary(
    tmp_path: Path,
    capsys,
) -> None:
    run_dir = tmp_path / "run-001"
    write_repr_lab_run(run_dir)

    exit_code = main(
        [
            "inspect-experiment",
            "--source-kind",
            "repr_lab_run_directory",
            "--source-path",
            str(run_dir),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["bundle_id"] == "run-001"
    assert payload["metric_table"]["row_count"] == 2
    assert payload["metadata"]["model_family"] == "vjepa2"


def test_render_figure_cli_writes_dataset_figure_and_manifest(
    tmp_path: Path,
    capsys,
) -> None:
    bundle_dir = tmp_path / "bundle"
    write_release_bundle(bundle_dir)
    spec_path = tmp_path / "dataset_spec.json"
    spec_path.write_text(
        json.dumps(
                {
                    "spec_id": "dataset-category-counts",
                    "figure_kind": "dataset_category_counts",
                    "title": "Category counts",
                    "subtitle": "Published release bundle",
                    "bundle_dir": str(bundle_dir),
                    "output_stem": "dataset-category-counts",
                }
            ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "artifacts"

    exit_code = main(
        [
            "render-figure",
            "--spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    figure_path = Path(payload["figure_path"])
    manifest_path = Path(payload["manifest_path"])
    assert figure_path.exists()
    assert figure_path.suffix == ".png"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["spec"]["figure_kind"] == "dataset_category_counts"
    assert manifest["input_bundle"]["dataset_view"]["annotation_count"] == 1
    assert manifest["series"] == [{"label": "signal-object", "value": 1}]
    for export in manifest["exports"]:
        assert not Path(export["path"]).is_absolute(), "manifest exports should use relative paths"


def test_render_figure_cli_supports_plotly_html_output(
    tmp_path: Path,
    capsys,
) -> None:
    bundle_dir = tmp_path / "bundle"
    write_release_bundle(bundle_dir)
    spec_path = tmp_path / "dataset_plotly_spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "spec_id": "dataset-category-counts-plotly",
                "figure_kind": "dataset_category_counts",
                "title": "Category counts",
                "subtitle": "Interactive release bundle view",
                "bundle_dir": str(bundle_dir),
                "backend": "plotly",
                "output_stem": "dataset-category-counts-plotly",
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "artifacts"

    exit_code = main(
        [
            "render-figure",
            "--spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    figure_path = Path(payload["figure_path"])
    manifest = json.loads(Path(payload["manifest_path"]).read_text(encoding="utf-8"))
    assert payload["backend"] == "plotly"
    assert payload["output_format"] == "html"
    assert figure_path.exists()
    assert figure_path.suffix == ".html"
    assert manifest["rendering"] == {"backend": "plotly", "output_format": "html"}
    assert manifest["exports"][0]["artifact_kind"] == "interactive_figure"
    assert manifest["exports"][0]["media_type"] == "text/html"


def test_render_figure_cli_supports_raw_lvis_dataset(
    tmp_path: Path,
    capsys,
) -> None:
    dataset_path = tmp_path / "lvis.json"
    write_raw_lvis_dataset(dataset_path)
    spec_path = tmp_path / "lvis_spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "spec_id": "lvis-category-counts",
                "figure_kind": "dataset_category_counts",
                "title": "LVIS category counts",
                "dataset_source_kind": "lvis",
                "dataset_path": str(dataset_path),
                "task_type": "instance_segmentation",
                "output_stem": "lvis-category-counts",
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "artifacts"

    exit_code = main(
        [
            "render-figure",
            "--spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    manifest = json.loads(Path(payload["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["spec"]["dataset_source_kind"] == "lvis"
    assert manifest["input_bundle"]["dataset_view"]["source_kind"] == "lvis"
    assert manifest["series"] == [{"label": "rare-object", "value": 1}]


def test_render_figure_cli_supports_pascal_voc_dataset(
    tmp_path: Path,
    capsys,
) -> None:
    dataset_root = tmp_path / "voc"
    write_pascal_voc_dataset(dataset_root)
    spec_path = tmp_path / "voc_spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "spec_id": "voc-category-counts",
                "figure_kind": "dataset_category_counts",
                "title": "VOC category counts",
                "dataset_source_kind": "pascal_voc",
                "dataset_path": str(dataset_root),
                "output_stem": "voc-category-counts",
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "artifacts"

    exit_code = main(
        [
            "render-figure",
            "--spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    manifest = json.loads(Path(payload["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["spec"]["dataset_source_kind"] == "pascal_voc"
    assert manifest["input_bundle"]["dataset_view"]["source_kind"] == "pascal_voc"
    assert manifest["series"] == [{"label": "signal-object", "value": 1}]


def test_render_figure_cli_writes_experiment_figure_and_manifest(
    tmp_path: Path,
    capsys,
) -> None:
    metric_table_path = tmp_path / "metrics.csv"
    write_metric_table(metric_table_path)
    spec_path = tmp_path / "experiment_spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "spec_id": "accuracy-by-model",
                "figure_kind": "experiment_metric_bars",
                "title": "Accuracy by model",
                "metric_table_path": str(metric_table_path),
                "metric": "accuracy",
                "group_by": "model",
                "output_stem": "accuracy-by-model",
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "artifacts"

    exit_code = main(
        [
            "render-figure",
            "--spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    manifest_path = Path(payload["manifest_path"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["spec"]["figure_kind"] == "experiment_metric_bars"
    assert manifest["input_bundle"]["metric_table"]["row_count"] == 3
    assert manifest["series"] == [
        {"label": "vjepa", "value": 0.91},
        {"label": "sam", "value": 0.84},
    ]


def test_render_figure_cli_supports_matplotlib_pdf_output(
    tmp_path: Path,
    capsys,
) -> None:
    metric_table_path = tmp_path / "metrics.csv"
    write_metric_table(metric_table_path)
    spec_path = tmp_path / "experiment_pdf_spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "spec_id": "accuracy-by-model-pdf",
                "figure_kind": "experiment_metric_bars",
                "title": "Accuracy by model",
                "metric_table_path": str(metric_table_path),
                "metric": "accuracy",
                "group_by": "model",
                "output_format": "pdf",
                "output_stem": "accuracy-by-model-pdf",
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "artifacts"

    exit_code = main(
        [
            "render-figure",
            "--spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    figure_path = Path(payload["figure_path"])
    manifest = json.loads(Path(payload["manifest_path"]).read_text(encoding="utf-8"))
    assert payload["backend"] == "matplotlib"
    assert payload["output_format"] == "pdf"
    assert figure_path.exists()
    assert figure_path.suffix == ".pdf"
    assert manifest["rendering"] == {"backend": "matplotlib", "output_format": "pdf"}
    assert manifest["exports"][0]["artifact_kind"] == "static_figure"
    assert manifest["exports"][0]["media_type"] == "application/pdf"


def test_render_figure_cli_supports_repr_lab_run_directory(
    tmp_path: Path,
    capsys,
) -> None:
    run_dir = tmp_path / "run-001"
    write_repr_lab_run(run_dir)
    spec_path = tmp_path / "repr_spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "spec_id": "repr-top1-accuracy",
                "figure_kind": "experiment_metric_bars",
                "title": "repr-lab top1 accuracy",
                "experiment_source_kind": "repr_lab_run_directory",
                "experiment_path": str(run_dir),
                "metric": "top1_accuracy",
                "group_by": "model_variant",
                "output_stem": "repr-top1-accuracy",
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "artifacts"

    exit_code = main(
        [
            "render-figure",
            "--spec",
            str(spec_path),
            "--output-dir",
            str(output_dir),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    manifest = json.loads(Path(payload["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["spec"]["experiment_source_kind"] == "repr_lab_run_directory"
    assert (
        manifest["input_bundle"]["metadata"]["benchmark_task"]
        == "frozen-feature-localization-probe"
    )
    assert manifest["series"] == [{"label": "vjepa2-vitl16", "value": 0.91}]
