# Runbooks

Technical guide for local setup, dependency validation, and runtime notes.

## Bootstrap

Use Python `3.13` for now.

```bash
just setup
```

## Validation

```bash
python -m fig_lab.main --version
python -m fig_lab.main smoke
python -m fig_lab.smoke
python -m pytest -q
```

## Runtime Notes

- `src/fig_lab/contracts.py` defines the normalized Python record types
- `inspect-release` currently exercises the preferred release-bundle reader
  path
- `inspect-dataset --source-kind <kind> --source-path <path>` exercises the raw dataset reader path for `coco`, `lvis`, and `pascal_voc`
- `inspect-experiment --source-kind <kind> --source-path <path>` exercises the experiment reader path for `standalone_metric_table` and the bounded `repr_lab_run_directory` contract
- `render-figure --spec /path/to/spec.json --output-dir /path/to/artifacts` is the end-to-end figure/export path for static and interactive outputs
- keep renderer selection behind the normalized record layer so plotting backends do not parse raw formats directly

## Figure Spec Notes

`render-figure` currently supports two spec kinds:

- `dataset_category_counts`: bar chart from a published release bundle or a raw `COCO`, `LVIS`, or `PASCAL VOC` dataset source
- `experiment_metric_bars`: grouped metric bars from a standalone metrics table
  or a manifest-backed `repr-lab` run directory

Each spec may set:

- `backend`: `matplotlib` or `plotly`
- `output_format`: `png`, `svg`, or `pdf` for `matplotlib`; `html` for `plotly`

Defaults:

- `matplotlib` defaults to `png`
- `plotly` defaults to `html`

Minimal dataset spec:

```json
{
  "spec_id": "dataset-category-counts",
  "figure_kind": "dataset_category_counts",
  "title": "Category counts",
  "bundle_dir": "/path/to/release-bundle",
  "output_stem": "dataset-category-counts"
}
```

Raw dataset variant:

```json
{
  "spec_id": "voc-category-counts",
  "figure_kind": "dataset_category_counts",
  "title": "VOC category counts",
  "dataset_source_kind": "pascal_voc",
  "dataset_path": "/path/to/voc-root",
  "output_stem": "voc-category-counts"
}
```

Minimal experiment spec:

```json
{
  "spec_id": "accuracy-by-model",
  "figure_kind": "experiment_metric_bars",
  "title": "Accuracy by model",
  "metric_table_path": "/path/to/metrics.csv",
  "metric": "accuracy",
  "group_by": "model",
  "output_stem": "accuracy-by-model"
}
```

`repr-lab` run-directory variant:

```json
{
  "spec_id": "repr-top1-accuracy",
  "figure_kind": "experiment_metric_bars",
  "title": "repr-lab top1 accuracy",
  "experiment_source_kind": "repr_lab_run_directory",
  "experiment_path": "/path/to/repr-run",
  "metric": "top1_accuracy",
  "group_by": "model_variant",
  "output_stem": "repr-top1-accuracy"
}
```

Interactive `plotly` variant:

```json
{
  "spec_id": "repr-top1-accuracy-interactive",
  "figure_kind": "experiment_metric_bars",
  "title": "repr-lab top1 accuracy",
  "experiment_source_kind": "repr_lab_run_directory",
  "experiment_path": "/path/to/repr-run",
  "metric": "top1_accuracy",
  "group_by": "model_variant",
  "backend": "plotly",
  "output_stem": "repr-top1-accuracy-interactive"
}
```

Metric tables must include:

- `metric`
- `value`
- `source_artifact`
- `source_run_id`
