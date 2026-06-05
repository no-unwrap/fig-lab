"""Experiment readers for standalone metric tables and repr-lab run directories.

Each public loader returns a ``FigureInputBundle`` wrapping a normalized
``MetricTable``.  The repr-lab reader validates the bounded
``repr_lab_run_directory_contract@1.0.0`` before extracting metrics.
"""

from __future__ import annotations

from pathlib import Path

from fig_lab._parsing import coerce_object, load_json_object, require_keys, string_or_none
from fig_lab._source_kinds import (
    REPR_LAB_RUN_DIRECTORY,
    STANDALONE_METRIC_TABLE,
    SUPPORTED_EXPERIMENT_SOURCE_KINDS,
)
from fig_lab.contracts import FigureInputBundle, MetricRecord, MetricTable
from fig_lab.metric_reader import load_metric_table_bundle

RUN_DIRECTORY_CONTRACT_NAME = "repr_lab_run_directory_contract"
RUN_DIRECTORY_CONTRACT_VERSION = "1.0.0"
RUN_DIRECTORY_KIND = "benchmark_run_directory"
RUN_DIRECTORY_PRODUCER_REPO = "repr-lab"
REQUIRED_MANIFEST_KEYS = (
    "contract_name",
    "contract_version",
    "run_directory_kind",
    "producer_repo",
    "name",
    "dataset",
    "model",
    "seed",
    "run_id",
    "created_at",
)
REQUIRED_BENCHMARK_RESULT_KEYS = (
    "contract_name",
    "contract_version",
    "run_directory_kind",
    "producer_repo",
    "schema_version",
    "run_id",
    "release_id",
    "release_version",
    "benchmark_task",
    "model_family",
    "model_variant",
    "status",
    "started_at",
    "artifact_paths",
)


def load_experiment_bundle(
    source_kind: str,
    source_path: str | Path,
) -> FigureInputBundle:
    """Load an experiment from *source_kind* at *source_path* into a normalized bundle."""
    normalized_source_kind = _normalize_source_kind(source_kind)
    if normalized_source_kind == STANDALONE_METRIC_TABLE:
        return load_metric_table_bundle(source_path)
    if normalized_source_kind == REPR_LAB_RUN_DIRECTORY:
        return load_repr_lab_run_directory(source_path)
    raise ValueError(f"unsupported experiment source_kind: {source_kind}")


def load_repr_lab_run_directory(run_dir: str | Path) -> FigureInputBundle:
    """Load metrics from a bounded repr-lab run directory."""
    resolved_run_dir = Path(run_dir).resolve()
    manifest_path = resolved_run_dir / "manifest.json"
    benchmark_result_path = resolved_run_dir / "benchmark_result.json"
    if not manifest_path.exists():
        raise ValueError(f"missing repr-lab manifest: {manifest_path}")
    if not benchmark_result_path.exists():
        raise ValueError(f"missing repr-lab benchmark result: {benchmark_result_path}")

    manifest = load_json_object(manifest_path)
    benchmark_result = load_json_object(benchmark_result_path)
    _validate_run_directory_contract(manifest, benchmark_result)
    metrics = coerce_object(benchmark_result.get("metrics"))
    run_id = _require_string(benchmark_result, "run_id")
    manifest_run_id = string_or_none(manifest.get("run_id"))
    if manifest_run_id is not None and manifest_run_id != run_id:
        raise ValueError("repr-lab manifest run_id does not match benchmark_result run_id")

    release_id = _require_string(benchmark_result, "release_id")
    release_version = _require_string(benchmark_result, "release_version")
    benchmark_task = _require_string(benchmark_result, "benchmark_task")
    model_family = _require_string(benchmark_result, "model_family")
    model_variant = _require_string(benchmark_result, "model_variant")
    status = _require_string(benchmark_result, "status")
    artifact_paths = coerce_object(benchmark_result.get("artifact_paths") or {})

    metric_rows = [
        MetricRecord(
            metric=metric_name,
            value=_coerce_metric_value(metric_value, metric_name=metric_name),
            source_artifact=str(benchmark_result_path),
            source_run_id=run_id,
            dataset_id=release_id,
            model=f"{model_family}:{model_variant}",
            model_family=model_family,
            model_variant=model_variant,
            run_id=run_id,
            benchmark_task=benchmark_task,
            status=status,
            metadata={"release_version": release_version},
        )
        for metric_name, metric_value in sorted(metrics.items())
    ]

    source_artifacts = [str(manifest_path), str(benchmark_result_path)]
    result_path = resolved_run_dir / "result.json"
    if result_path.exists():
        source_artifacts.append(str(result_path))
    for artifact_path in artifact_paths.values():
        resolved_artifact = _resolve_artifact_path(artifact_path, run_dir=resolved_run_dir)
        if not resolved_artifact.exists():
            raise ValueError(f"missing repr-lab declared artifact: {resolved_artifact}")
        source_artifacts.append(str(resolved_artifact))

    lineage = [
        {"source_kind": REPR_LAB_RUN_DIRECTORY, "source_artifact": str(manifest_path)},
        {"source_kind": REPR_LAB_RUN_DIRECTORY, "source_artifact": str(benchmark_result_path)},
    ]
    metric_table = MetricTable(
        rows=metric_rows,
        lineage=lineage,
        metadata={
            "source_kind": REPR_LAB_RUN_DIRECTORY,
            "manifest_path": str(manifest_path),
            "benchmark_result_path": str(benchmark_result_path),
            "release_id": release_id,
            "release_version": release_version,
            "benchmark_task": benchmark_task,
            "model_family": model_family,
            "model_variant": model_variant,
            "status": status,
        },
    )
    return FigureInputBundle(
        bundle_id=run_id,
        bundle_kind="metric_table",
        source_artifacts=_dedupe_preserving_order(source_artifacts),
        lineage=lineage,
        metric_table=metric_table,
        metadata=metric_table.metadata,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalize_source_kind(source_kind: str) -> str:
    normalized = source_kind.strip().lower().replace("-", "_")
    if normalized not in SUPPORTED_EXPERIMENT_SOURCE_KINDS:
        raise ValueError(f"unsupported experiment source_kind: {source_kind}")
    return normalized


def _validate_run_directory_contract(
    manifest: dict[str, object],
    benchmark_result: dict[str, object],
) -> None:
    require_keys(manifest, REQUIRED_MANIFEST_KEYS, label="repr-lab manifest")
    require_keys(
        benchmark_result,
        REQUIRED_BENCHMARK_RESULT_KEYS,
        label="repr-lab benchmark_result",
    )
    for payload_label, payload in (
        ("repr-lab manifest", manifest),
        ("repr-lab benchmark_result", benchmark_result),
    ):
        if str(payload["contract_name"]) != RUN_DIRECTORY_CONTRACT_NAME:
            raise ValueError(f"{payload_label} has unsupported contract_name")
        if str(payload["contract_version"]) != RUN_DIRECTORY_CONTRACT_VERSION:
            raise ValueError(f"{payload_label} has unsupported contract_version")
        if str(payload["run_directory_kind"]) != RUN_DIRECTORY_KIND:
            raise ValueError(f"{payload_label} has unsupported run_directory_kind")
        if str(payload["producer_repo"]) != RUN_DIRECTORY_PRODUCER_REPO:
            raise ValueError(f"{payload_label} has unsupported producer_repo")


def _require_string(payload: dict[str, object], key: str) -> str:
    value = string_or_none(payload.get(key))
    if value is None:
        raise ValueError(f"repr-lab result is missing required field {key!r}")
    return value


def _coerce_metric_value(value: object, *, metric_name: str) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"repr-lab metric {metric_name!r} must be numeric")
    return float(value)


def _resolve_artifact_path(value: object, *, run_dir: Path) -> Path:
    artifact_path = string_or_none(value)
    if artifact_path is None:
        raise ValueError("repr-lab artifact_paths entries must be non-empty strings")
    candidate = Path(artifact_path)
    return candidate.resolve() if candidate.is_absolute() else (run_dir / candidate).resolve()


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped
