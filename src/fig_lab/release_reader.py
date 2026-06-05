"""Published release bundle reader.

Validates the ``published_artifact_bundle_contract`` manifest and delegates
COCO-format annotation parsing to the shared dataset normalization layer.
"""

from __future__ import annotations

from pathlib import Path

from fig_lab._coco_normalization import build_annotations, build_assets, build_categories
from fig_lab._parsing import (
    coerce_list,
    coerce_object,
    coerce_optional_object,
    load_json_object,
    require_keys,
)
from fig_lab._source_kinds import PUBLISHED_RELEASE_BUNDLE
from fig_lab.contracts import DatasetView, FigureInputBundle

PRIMARY_CONTRACT_NAME = "published_artifact_bundle_contract"
SUPPORTED_CONTRACT_NAMES = {PRIMARY_CONTRACT_NAME}
PRIMARY_BUNDLE_KIND = "dataset_release_bundle"
SUPPORTED_BUNDLE_KINDS = {PRIMARY_BUNDLE_KIND}
SUPPORTED_MAJOR_VERSION = "1"
REQUIRED_MANIFEST_KEYS = (
    "contract_name",
    "contract_version",
    "bundle_kind",
    "release_id",
    "release_version",
    "task_types",
    "artifact_paths",
    "lineage",
)
REQUIRED_ARTIFACT_KEYS = (
    "annotations_coco",
    "assets_table",
    "categories_table",
)


def load_published_release_bundle(bundle_dir: str | Path) -> FigureInputBundle:
    """Load a published release bundle from *bundle_dir* into a normalized dataset bundle."""
    resolved_bundle_dir = Path(bundle_dir).resolve()
    manifest = load_json_object(resolved_bundle_dir / "release_manifest.json")
    require_keys(manifest, REQUIRED_MANIFEST_KEYS)
    _validate_contract(manifest)

    artifact_paths = coerce_object(manifest["artifact_paths"])
    require_keys(artifact_paths, REQUIRED_ARTIFACT_KEYS)
    resolved_artifact_paths = {
        key: str((resolved_bundle_dir / str(value)).resolve())
        for key, value in artifact_paths.items()
    }
    for key in REQUIRED_ARTIFACT_KEYS:
        artifact_path = Path(resolved_artifact_paths[key])
        if not artifact_path.exists():
            raise ValueError(f"missing declared artifact for {key}: {artifact_path}")

    annotations_path = Path(resolved_artifact_paths["annotations_coco"])
    annotations_payload = load_json_object(annotations_path)
    assets = build_assets(
        coerce_list(annotations_payload.get("images")),
        image_root=annotations_path.parent,
    )
    categories = build_categories(coerce_list(annotations_payload.get("categories")))
    category_names = {category.category_id: category.name for category in categories}
    annotations = build_annotations(
        coerce_list(annotations_payload.get("annotations")),
        category_names=category_names,
    )
    dataset_info = coerce_optional_object(manifest.get("dataset"))
    dataset_view = DatasetView(
        dataset_id=str(dataset_info.get("dataset_id") or manifest["release_id"]),
        dataset_version=str(dataset_info.get("dataset_version") or manifest["release_version"]),
        source_kind=PUBLISHED_RELEASE_BUNDLE,
        task_types=[str(task_type) for task_type in coerce_list(manifest["task_types"])],
        assets=assets,
        categories=categories,
        annotations=annotations,
        lineage=[
            coerce_object(entry)
            for entry in coerce_list(manifest["lineage"])
            if isinstance(entry, dict)
        ],
        metadata={
            "release_id": str(manifest["release_id"]),
            "release_version": str(manifest["release_version"]),
            "publisher_repo": str(manifest.get("publisher_repo") or ""),
            "publisher_commit_sha": str(manifest.get("publisher_commit_sha") or ""),
        },
    )
    return FigureInputBundle(
        bundle_id=str(manifest["release_id"]),
        bundle_kind="dataset_view",
        source_artifacts=list(resolved_artifact_paths.values()),
        lineage=dataset_view.lineage,
        dataset_view=dataset_view,
        metadata={
            "release_bundle_kind": str(manifest["bundle_kind"]),
            "contract_version": str(manifest["contract_version"]),
        },
    )


def _validate_contract(manifest: dict[str, object]) -> None:
    if str(manifest["contract_name"]) not in SUPPORTED_CONTRACT_NAMES:
        raise ValueError("unsupported contract_name")
    if str(manifest["bundle_kind"]) not in SUPPORTED_BUNDLE_KINDS:
        raise ValueError("unsupported bundle_kind")
    contract_version = str(manifest["contract_version"])
    if contract_version.split(".", 1)[0] != SUPPORTED_MAJOR_VERSION:
        raise ValueError("unsupported contract_version major")


def load_label_lab_release_bundle(bundle_dir: str | Path) -> FigureInputBundle:
    """Convenience alias for ``load_published_release_bundle``."""
    return load_published_release_bundle(bundle_dir)
