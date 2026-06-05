"""Dataset readers for published release bundles and raw annotation formats.

Each public loader returns a ``FigureInputBundle`` wrapping a normalized
``DatasetView``.  Source-specific parsing is handled internally; callers
interact only with the canonical contract types defined in ``contracts``.
"""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from fig_lab._coco_normalization import (
    build_annotations,
    build_assets,
    build_categories,
    resolve_image_path,
)
from fig_lab._parsing import coerce_list, coerce_optional_object, load_json_object, string_or_none
from fig_lab._source_kinds import (
    COCO,
    LVIS,
    PASCAL_VOC,
    PUBLISHED_RELEASE_BUNDLE,
    SUPPORTED_DATASET_SOURCE_KINDS,
)
from fig_lab.contracts import (
    DatasetView,
    FigureInputBundle,
    VisualAnnotation,
    VisualAsset,
    VisualCategory,
)
from fig_lab.release_reader import load_published_release_bundle


def load_dataset_bundle(
    source_kind: str,
    source_path: str | Path,
) -> FigureInputBundle:
    """Load a dataset from *source_kind* at *source_path* into a normalized bundle."""
    normalized_source_kind = _normalize_source_kind(source_kind)
    if normalized_source_kind == PUBLISHED_RELEASE_BUNDLE:
        return load_published_release_bundle(source_path)
    if normalized_source_kind == COCO:
        return load_coco_dataset(source_path)
    if normalized_source_kind == LVIS:
        return load_lvis_dataset(source_path)
    if normalized_source_kind == PASCAL_VOC:
        return load_pascal_voc_dataset(source_path)
    raise ValueError(f"unsupported dataset source_kind: {source_kind}")


def load_coco_dataset(dataset_path: str | Path) -> FigureInputBundle:
    """Load a COCO-format annotation file into a normalized bundle."""
    return _load_coco_like_dataset(dataset_path, source_kind=COCO)


def load_lvis_dataset(dataset_path: str | Path) -> FigureInputBundle:
    """Load an LVIS-format annotation file into a normalized bundle."""
    return _load_coco_like_dataset(
        dataset_path,
        source_kind=LVIS,
        category_frequency_key="frequency",
    )


def load_pascal_voc_dataset(dataset_path: str | Path) -> FigureInputBundle:
    """Load Pascal VOC XML annotations into a normalized bundle."""
    resolved_dataset_path = Path(dataset_path).resolve()
    annotation_paths, image_root = _discover_pascal_voc_layout(resolved_dataset_path)
    if not annotation_paths:
        raise ValueError(f"no Pascal VOC annotation XML files found under {resolved_dataset_path}")

    assets: list[VisualAsset] = []
    annotations: list[VisualAnnotation] = []
    categories_by_name: dict[str, VisualCategory] = {}
    for annotation_path in annotation_paths:
        root = ET.parse(annotation_path).getroot()
        file_name = (
            string_or_none(root.findtext("filename"))
            or f"{annotation_path.stem}.jpg"
        )
        width = _xml_int(root.findtext("size/width"))
        height = _xml_int(root.findtext("size/height"))
        asset_id = annotation_path.stem
        assets.append(
            VisualAsset(
                asset_id=asset_id,
                file_name=file_name,
                image_path_or_uri=(
                    string_or_none(root.findtext("path"))
                    or resolve_image_path(file_name, image_root)
                ),
                width=width,
                height=height,
                source_asset_id=asset_id,
                metadata={"annotation_path": str(annotation_path)},
            )
        )

        for object_index, object_element in enumerate(root.findall("object"), start=1):
            category_name = _require_xml_text(
                object_element.findtext("name"),
                context=f"{annotation_path}: object {object_index}",
            )
            categories_by_name.setdefault(
                category_name,
                VisualCategory(category_id=category_name, name=category_name),
            )
            bbox_xywh = _voc_bbox_xywh(
                object_element.find("bndbox"),
                context=f"{annotation_path}: object {object_index}",
            )
            annotation_metadata: dict[str, object] = {}
            difficult = _optional_xml_int(object_element.findtext("difficult"))
            truncated = _optional_xml_int(object_element.findtext("truncated"))
            pose = string_or_none(object_element.findtext("pose"))
            if difficult is not None:
                annotation_metadata["difficult"] = difficult
            if truncated is not None:
                annotation_metadata["truncated"] = truncated
            if pose is not None:
                annotation_metadata["pose"] = pose
            annotations.append(
                VisualAnnotation(
                    annotation_id=f"{asset_id}:{object_index}",
                    asset_id=asset_id,
                    category_id=category_name,
                    category_name=category_name,
                    task_type="bbox",
                    bbox_xywh=bbox_xywh,
                    area=round(bbox_xywh[2] * bbox_xywh[3], 6),
                    source_annotation_id=f"{annotation_path.name}:{object_index}",
                    metadata=annotation_metadata,
                )
            )

    dataset_id = resolved_dataset_path.stem
    dataset_view = DatasetView(
        dataset_id=dataset_id,
        dataset_version=None,
        source_kind=PASCAL_VOC,
        task_types=["bbox"] if annotations else [],
        assets=assets,
        categories=sorted(categories_by_name.values(), key=lambda category: category.name),
        annotations=annotations,
        lineage=[{"source_kind": PASCAL_VOC, "source_artifact": str(resolved_dataset_path)}],
        metadata={
            "annotation_file_count": len(annotation_paths),
            "source_path": str(resolved_dataset_path),
        },
    )
    return FigureInputBundle(
        bundle_id=dataset_id,
        bundle_kind="dataset_view",
        source_artifacts=[str(path) for path in annotation_paths],
        lineage=dataset_view.lineage,
        dataset_view=dataset_view,
        metadata={"input_source_kind": PASCAL_VOC},
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_coco_like_dataset(
    dataset_path: str | Path,
    *,
    source_kind: str,
    category_frequency_key: str | None = None,
) -> FigureInputBundle:
    """Shared loader for COCO and LVIS annotation files."""
    resolved_dataset_path = Path(dataset_path).resolve()
    payload = load_json_object(resolved_dataset_path)
    assets = build_assets(
        coerce_list(payload.get("images")),
        image_root=resolved_dataset_path.parent,
    )
    categories = build_categories(
        coerce_list(payload.get("categories")),
        category_frequency_key=category_frequency_key,
    )
    category_names = {category.category_id: category.name for category in categories}
    annotations = build_annotations(
        coerce_list(payload.get("annotations")),
        category_names=category_names,
    )
    info = coerce_optional_object(payload.get("info"))
    dataset_id = (
        string_or_none(info.get("dataset_id"))
        or string_or_none(info.get("name"))
        or string_or_none(info.get("description"))
        or resolved_dataset_path.stem
    )
    dataset_view = DatasetView(
        dataset_id=dataset_id,
        dataset_version=(
            string_or_none(info.get("version"))
            or string_or_none(info.get("year"))
        ),
        source_kind=source_kind,
        task_types=sorted({annotation.task_type for annotation in annotations}),
        assets=assets,
        categories=categories,
        annotations=annotations,
        lineage=[{"source_kind": source_kind, "source_artifact": str(resolved_dataset_path)}],
        metadata={"source_path": str(resolved_dataset_path)},
    )
    return FigureInputBundle(
        bundle_id=dataset_id,
        bundle_kind="dataset_view",
        source_artifacts=[str(resolved_dataset_path)],
        lineage=dataset_view.lineage,
        dataset_view=dataset_view,
        metadata={"input_source_kind": source_kind},
    )


def _discover_pascal_voc_layout(source_path: Path) -> tuple[list[Path], Path | None]:
    if source_path.is_file():
        return [source_path], source_path.parent

    annotations_dir = source_path / "Annotations"
    if annotations_dir.exists():
        annotation_paths = sorted(annotations_dir.glob("*.xml"))
        image_root = source_path / "JPEGImages"
        return annotation_paths, image_root if image_root.exists() else source_path

    return sorted(source_path.glob("*.xml")), source_path


def _voc_bbox_xywh(
    bbox_element: ET.Element | None,
    *,
    context: str,
) -> list[float]:
    if bbox_element is None:
        raise ValueError(f"missing Pascal VOC bndbox for {context}")
    xmin = _xml_float(bbox_element.findtext("xmin"), context=f"{context} xmin")
    ymin = _xml_float(bbox_element.findtext("ymin"), context=f"{context} ymin")
    xmax = _xml_float(bbox_element.findtext("xmax"), context=f"{context} xmax")
    ymax = _xml_float(bbox_element.findtext("ymax"), context=f"{context} ymax")
    width = xmax - xmin
    height = ymax - ymin
    if width <= 0 or height <= 0:
        raise ValueError(f"invalid Pascal VOC bbox extents for {context}")
    return [xmin, ymin, width, height]


def _normalize_source_kind(source_kind: str) -> str:
    normalized = source_kind.strip().lower().replace("-", "_")
    if normalized not in SUPPORTED_DATASET_SOURCE_KINDS:
        raise ValueError(f"unsupported dataset source_kind: {source_kind}")
    return normalized


def _require_xml_text(value: str | None, *, context: str) -> str:
    normalized = string_or_none(value)
    if normalized is None:
        raise ValueError(f"missing required text for {context}")
    return normalized


def _xml_int(value: str | None) -> int:
    return int(_require_xml_text(value, context="Pascal VOC integer field"))


def _optional_xml_int(value: str | None) -> int | None:
    normalized = string_or_none(value)
    if normalized is None:
        return None
    return int(normalized)


def _xml_float(value: str | None, *, context: str) -> float:
    return float(_require_xml_text(value, context=context))
