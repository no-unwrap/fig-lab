"""Figure renderer and export manifest builder.

Takes a validated ``FigureSpec`` and its loaded ``FigureInputBundle``, produces
an artifact-backed figure output, and writes a companion JSON export manifest
that records the full provenance chain from source artifacts through to the
rendered output.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Callable
from html import escape
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt  # noqa: E402

from fig_lab.contracts import FigureInputBundle
from fig_lab.dataset_reader import load_dataset_bundle
from fig_lab.experiment_reader import load_experiment_bundle
from fig_lab.figure_spec import (
    DATASET_CATEGORY_COUNTS,
    EXPERIMENT_METRIC_BARS,
    DatasetCategoryCountFigureSpec,
    ExperimentMetricBarFigureSpec,
    FigureSpec,
    load_figure_spec,
)

EXPORT_MANIFEST_VERSION = "1.0.0"
OUTPUT_ARTIFACT_KIND = {
    "png": "static_figure",
    "svg": "static_figure",
    "pdf": "static_figure",
    "html": "interactive_figure",
}
OUTPUT_MEDIA_TYPE = {
    "png": "image/png",
    "svg": "image/svg+xml",
    "pdf": "application/pdf",
    "html": "text/html",
}
SUPPORTED_GROUP_FIELDS = {
    "dataset_id",
    "split",
    "cohort",
    "model",
    "model_family",
    "model_variant",
    "run_id",
    "group",
    "source_run_id",
    "benchmark_task",
    "status",
}

# ---------------------------------------------------------------------------
# Renderer registry
# ---------------------------------------------------------------------------

SeriesAndBundle = tuple[list[dict[str, object]], FigureInputBundle]
RenderFn = Callable[[FigureSpec, Path], SeriesAndBundle]

_RENDERERS: dict[str, RenderFn] = {}


def _register_renderer(figure_kind: str) -> Callable[[RenderFn], RenderFn]:
    """Decorator that registers a per-kind render function."""

    def decorator(fn: RenderFn) -> RenderFn:
        _RENDERERS[figure_kind] = fn
        return fn

    return decorator


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_figure_from_spec_path(
    spec_path: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    """Load a figure spec from *spec_path*, render it, and return a CLI summary."""
    resolved_spec_path = Path(spec_path).resolve()
    spec = load_figure_spec(resolved_spec_path)
    return render_figure(spec, output_dir, spec_path=resolved_spec_path)


def render_figure(
    spec: FigureSpec,
    output_dir: str | Path,
    *,
    spec_path: str | Path | None = None,
) -> dict[str, object]:
    """Render a figure from *spec* into *output_dir* and return a CLI summary."""
    output_root = Path(output_dir).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    figure_path = output_root / f"{spec.output_stem}.{spec.output_format}"
    manifest_path = output_root / f"{spec.output_stem}.manifest.json"

    renderer = _RENDERERS.get(spec.figure_kind)
    if renderer is None:
        raise ValueError(f"unsupported figure spec: {spec.figure_kind}")

    series, bundle = renderer(spec, figure_path)
    manifest = _build_manifest(
        spec=spec,
        spec_path=spec_path,
        figure_path=figure_path,
        manifest_path=manifest_path,
        output_dir=output_root,
        input_bundle=bundle.to_summary_dict(),
        lineage=bundle.lineage,
        series=series,
    )
    _write_json(manifest_path, manifest)
    return _build_cli_summary(spec, figure_path, manifest_path, len(series))


# ---------------------------------------------------------------------------
# Per-kind renderers
# ---------------------------------------------------------------------------


@_register_renderer(DATASET_CATEGORY_COUNTS)
def _render_dataset_category_counts(
    spec: FigureSpec,
    figure_path: Path,
) -> SeriesAndBundle:
    assert isinstance(spec, DatasetCategoryCountFigureSpec)
    bundle = load_dataset_bundle(spec.dataset_source_kind, spec.dataset_path)
    series = _dataset_category_series(bundle, spec)
    _render_horizontal_bar_chart(
        backend=spec.backend,
        output_format=spec.output_format,
        figure_path=figure_path,
        title=spec.title,
        subtitle=spec.subtitle,
        x_label="Annotation count",
        labels=[item["label"] for item in series],
        values=[item["value"] for item in series],
        width=spec.width,
        height=spec.height,
    )
    return series, bundle


@_register_renderer(EXPERIMENT_METRIC_BARS)
def _render_experiment_metric_bars(
    spec: FigureSpec,
    figure_path: Path,
) -> SeriesAndBundle:
    assert isinstance(spec, ExperimentMetricBarFigureSpec)
    bundle = load_experiment_bundle(spec.experiment_source_kind, spec.experiment_path)
    series = _experiment_metric_series(bundle, spec)
    _render_horizontal_bar_chart(
        backend=spec.backend,
        output_format=spec.output_format,
        figure_path=figure_path,
        title=spec.title,
        subtitle=spec.subtitle,
        x_label=spec.metric,
        labels=[item["label"] for item in series],
        values=[item["value"] for item in series],
        width=spec.width,
        height=spec.height,
    )
    return series, bundle


# ---------------------------------------------------------------------------
# Series builders
# ---------------------------------------------------------------------------


def _dataset_category_series(
    bundle: FigureInputBundle,
    spec: DatasetCategoryCountFigureSpec,
) -> list[dict[str, object]]:
    """Build ranked (label, count) pairs from a dataset bundle's annotations."""
    dataset_view = bundle.dataset_view
    if dataset_view is None:
        raise ValueError("dataset bundle is missing dataset_view")

    counts: Counter[str] = Counter()
    for annotation in dataset_view.annotations:
        if spec.task_type is not None and annotation.task_type != spec.task_type:
            continue
        label = annotation.category_name or annotation.category_id or "uncategorized"
        counts[label] += 1

    if not counts:
        raise ValueError("dataset figure spec produced no category counts")

    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    if spec.top_n is not None:
        ranked = ranked[: spec.top_n]
    return [
        {"label": label, "value": value}
        for label, value in ranked
    ]


def _experiment_metric_series(
    bundle: FigureInputBundle,
    spec: ExperimentMetricBarFigureSpec,
) -> list[dict[str, object]]:
    """Build ranked (group, aggregated-value) pairs from an experiment bundle."""
    if spec.figure_kind != EXPERIMENT_METRIC_BARS:
        raise ValueError(f"unsupported experiment figure kind: {spec.figure_kind}")
    if spec.group_by not in SUPPORTED_GROUP_FIELDS:
        raise ValueError(f"unsupported experiment group_by: {spec.group_by}")
    if spec.aggregation != "mean":
        raise ValueError(f"unsupported aggregation: {spec.aggregation}")
    metric_table = bundle.metric_table
    if metric_table is None:
        raise ValueError("metric bundle is missing metric_table")

    grouped_values: dict[str, list[float]] = defaultdict(list)
    for row in metric_table.rows:
        if row.metric != spec.metric:
            continue
        group_value = getattr(row, spec.group_by)
        if group_value is None:
            raise ValueError(
                f"metric row for {spec.metric!r} is missing group_by value {spec.group_by!r}"
            )
        grouped_values[group_value].append(row.value)

    if not grouped_values:
        raise ValueError(f"experiment figure spec found no rows for metric {spec.metric!r}")

    ranked = sorted(
        (
            (label, sum(values) / len(values))
            for label, values in grouped_values.items()
        ),
        key=lambda item: (-item[1], item[0]),
    )
    return [
        {"label": label, "value": round(value, 6)}
        for label, value in ranked
    ]


# ---------------------------------------------------------------------------
# Backend rendering
# ---------------------------------------------------------------------------


def _render_horizontal_bar_chart(
    *,
    backend: str,
    output_format: str,
    figure_path: Path,
    title: str,
    subtitle: str | None,
    x_label: str,
    labels: list[str],
    values: list[float],
    width: float,
    height: float,
) -> None:
    if backend == "matplotlib":
        _render_horizontal_bar_chart_matplotlib(
            output_format=output_format,
            figure_path=figure_path,
            title=title,
            subtitle=subtitle,
            x_label=x_label,
            labels=labels,
            values=values,
            width=width,
            height=height,
        )
        return
    if backend == "plotly":
        _render_horizontal_bar_chart_plotly(
            figure_path=figure_path,
            title=title,
            subtitle=subtitle,
            x_label=x_label,
            labels=labels,
            values=values,
            width=width,
            height=height,
        )
        return
    raise ValueError(f"unsupported rendering backend: {backend}")


def _render_horizontal_bar_chart_matplotlib(
    *,
    output_format: str,
    figure_path: Path,
    title: str,
    subtitle: str | None,
    x_label: str,
    labels: list[str],
    values: list[float],
    width: float,
    height: float,
) -> None:
    figure, axis = plt.subplots(figsize=(width, height))
    axis.barh(labels, values, color="#355C7D")
    axis.set_title(title, loc="left")
    if subtitle:
        axis.text(
            0.0,
            1.02,
            subtitle,
            transform=axis.transAxes,
            ha="left",
            va="bottom",
        )
    axis.set_xlabel(x_label)
    axis.invert_yaxis()
    axis.grid(axis="x", linestyle="--", linewidth=0.5, alpha=0.35)
    figure.tight_layout()
    save_kwargs: dict[str, object] = {
        "bbox_inches": "tight",
        "format": output_format,
    }
    if output_format == "png":
        save_kwargs["dpi"] = 200
    figure.savefig(figure_path, **save_kwargs)
    plt.close(figure)


def _render_horizontal_bar_chart_plotly(
    *,
    figure_path: Path,
    title: str,
    subtitle: str | None,
    x_label: str,
    labels: list[str],
    values: list[float],
    width: float,
    height: float,
) -> None:
    from plotly import graph_objects as go

    title_text = escape(title)
    if subtitle:
        title_text = f"{title_text}<br><sup>{escape(subtitle)}</sup>"

    figure = go.Figure(
        data=[
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker={"color": "#355C7D"},
            )
        ]
    )
    figure.update_layout(
        template="plotly_white",
        title={"text": title_text, "x": 0.0, "xanchor": "left"},
        xaxis_title=x_label,
        yaxis={"autorange": "reversed"},
        width=max(int(width * 120), 320),
        height=max(int(height * 120), 240),
        margin={"l": 96, "r": 32, "t": 80, "b": 64},
    )
    figure.update_xaxes(showgrid=True, gridcolor="rgba(0, 0, 0, 0.12)")
    figure.write_html(figure_path, include_plotlyjs="cdn", full_html=True)


# ---------------------------------------------------------------------------
# Export manifest
# ---------------------------------------------------------------------------


def _build_manifest(
    *,
    spec: FigureSpec,
    spec_path: str | Path | None,
    figure_path: Path,
    manifest_path: Path,
    output_dir: Path,
    input_bundle: dict[str, object],
    lineage: list[dict[str, object]],
    series: list[dict[str, object]],
) -> dict[str, object]:
    manifest: dict[str, object] = {
        "manifest_version": EXPORT_MANIFEST_VERSION,
        "spec": spec.to_manifest_dict(),
        "input_bundle": input_bundle,
        "lineage": lineage,
        "series": series,
        "rendering": {
            "backend": spec.backend,
            "output_format": spec.output_format,
        },
        "exports": [
            {
                "artifact_kind": OUTPUT_ARTIFACT_KIND[spec.output_format],
                "media_type": OUTPUT_MEDIA_TYPE[spec.output_format],
                "path": str(figure_path.relative_to(output_dir)),
            },
            {
                "artifact_kind": "export_manifest",
                "media_type": "application/json",
                "path": str(manifest_path.relative_to(output_dir)),
            },
        ],
    }
    if spec_path is not None:
        manifest["spec_path"] = str(Path(spec_path).resolve())
    return manifest


def _build_cli_summary(
    spec: FigureSpec,
    figure_path: Path,
    manifest_path: Path,
    series_count: int,
) -> dict[str, object]:
    return {
        "spec_id": spec.spec_id,
        "figure_kind": spec.figure_kind,
        "backend": spec.backend,
        "output_format": spec.output_format,
        "figure_path": str(figure_path),
        "manifest_path": str(manifest_path),
        "series_count": series_count,
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
