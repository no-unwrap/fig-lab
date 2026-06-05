"""Error-path tests for figure spec validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fig_lab.figure_spec import load_figure_spec


def _write_spec(tmp_path: Path, payload: dict) -> Path:
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(payload), encoding="utf-8")
    return spec_path


def _minimal_dataset_spec(**overrides: object) -> dict:
    base = {
        "spec_id": "test",
        "figure_kind": "dataset_category_counts",
        "title": "Test",
        "bundle_dir": "/fake/bundle",
        "output_stem": "test",
    }
    base.update(overrides)
    return base


def _minimal_experiment_spec(**overrides: object) -> dict:
    base = {
        "spec_id": "test",
        "figure_kind": "experiment_metric_bars",
        "title": "Test",
        "metric_table_path": "/fake/metrics.csv",
        "metric": "accuracy",
        "group_by": "model",
        "output_stem": "test",
    }
    base.update(overrides)
    return base


def test_rejects_unsupported_figure_kind(tmp_path: Path) -> None:
    spec_path = _write_spec(tmp_path, {
        "spec_id": "test",
        "figure_kind": "unknown_kind",
        "title": "Test",
    })

    with pytest.raises(ValueError, match="unsupported figure_kind"):
        load_figure_spec(spec_path)


def test_rejects_unsupported_backend(tmp_path: Path) -> None:
    spec_path = _write_spec(tmp_path, _minimal_dataset_spec(backend="altair"))

    with pytest.raises(ValueError, match="unsupported backend"):
        load_figure_spec(spec_path)


def test_rejects_unsupported_output_format(tmp_path: Path) -> None:
    spec_path = _write_spec(tmp_path, _minimal_dataset_spec(output_format="jpeg"))

    with pytest.raises(ValueError, match="unsupported output_format"):
        load_figure_spec(spec_path)


def test_defaults_plotly_backend_to_html_output(tmp_path: Path) -> None:
    spec_path = _write_spec(tmp_path, _minimal_dataset_spec(backend="plotly"))

    spec = load_figure_spec(spec_path)

    assert spec.backend == "plotly"
    assert spec.output_format == "html"


def test_rejects_backend_output_format_mismatch(tmp_path: Path) -> None:
    spec_path = _write_spec(
        tmp_path,
        _minimal_dataset_spec(backend="plotly", output_format="png"),
    )

    with pytest.raises(ValueError, match="does not support output_format"):
        load_figure_spec(spec_path)


def test_rejects_negative_dimension(tmp_path: Path) -> None:
    spec_path = _write_spec(tmp_path, _minimal_dataset_spec(width=-1))

    with pytest.raises(ValueError, match="figure dimensions must be positive"):
        load_figure_spec(spec_path)


def test_rejects_invalid_top_n(tmp_path: Path) -> None:
    spec_path = _write_spec(tmp_path, _minimal_dataset_spec(top_n=-5))

    with pytest.raises(ValueError, match="top_n must be a positive integer"):
        load_figure_spec(spec_path)


def test_rejects_missing_dataset_path(tmp_path: Path) -> None:
    payload = _minimal_dataset_spec()
    del payload["bundle_dir"]
    spec_path = _write_spec(tmp_path, payload)

    with pytest.raises(ValueError, match="requires dataset_path or bundle_dir"):
        load_figure_spec(spec_path)


def test_rejects_bundle_dir_with_non_release_kind(tmp_path: Path) -> None:
    spec_path = _write_spec(
        tmp_path,
        _minimal_dataset_spec(dataset_source_kind="coco"),
    )

    with pytest.raises(ValueError, match="bundle_dir may only be used"):
        load_figure_spec(spec_path)


def test_rejects_missing_experiment_path(tmp_path: Path) -> None:
    payload = _minimal_experiment_spec()
    del payload["metric_table_path"]
    spec_path = _write_spec(tmp_path, payload)

    with pytest.raises(ValueError, match="requires experiment_path or metric_table_path"):
        load_figure_spec(spec_path)


def test_loads_valid_dataset_spec(tmp_path: Path) -> None:
    spec_path = _write_spec(tmp_path, _minimal_dataset_spec())

    spec = load_figure_spec(spec_path)

    assert spec.figure_kind == "dataset_category_counts"
    assert spec.spec_id == "test"


def test_loads_valid_experiment_spec(tmp_path: Path) -> None:
    spec_path = _write_spec(tmp_path, _minimal_experiment_spec())

    spec = load_figure_spec(spec_path)

    assert spec.figure_kind == "experiment_metric_bars"
    assert spec.metric == "accuracy"
