"""COCO/LVIS annotation normalization layer.

Converts raw COCO-style annotation payloads into the canonical
``contracts.VisualAsset``, ``contracts.VisualCategory``, and
``contracts.VisualAnnotation`` records that renderers consume.  Generic
JSON/string helpers live in ``_parsing``.
"""

from __future__ import annotations

from pathlib import Path

from fig_lab._parsing import coerce_object, string_or_none
from fig_lab.contracts import VisualAnnotation, VisualAsset, VisualCategory


def float_list_or_none(value: object) -> list[float] | None:
    """Return a ``list[float]`` if *value* is a non-empty numeric list, else ``None``."""
    if not isinstance(value, list) or not value:
        return None
    numbers: list[float] = []
    for item in value:
        if not isinstance(item, (int, float)):
            return None
        numbers.append(float(item))
    return numbers


def polygon_list(value: object) -> list[list[float]]:
    """Parse a COCO-style segmentation polygon list."""
    if not isinstance(value, list):
        return []
    polygons: list[list[float]] = []
    for polygon in value:
        if not isinstance(polygon, list):
            continue
        converted: list[float] = []
        for item in polygon:
            if not isinstance(item, (int, float)):
                converted = []
                break
            converted.append(float(item))
        if converted:
            polygons.append(converted)
    return polygons


def resolve_image_path(file_name: str, image_root: Path | None) -> str | None:
    """Resolve an image filename against *image_root*, returning ``None`` on failure."""
    if not file_name:
        return None
    candidate = Path(file_name)
    if candidate.is_absolute():
        return str(candidate)
    if image_root is not None:
        resolved = (image_root / candidate).resolve()
        if resolved.exists():
            return str(resolved)
    return file_name


def build_assets(
    images: list[object],
    *,
    image_root: Path | None,
) -> list[VisualAsset]:
    """Build ``VisualAsset`` records from a COCO-style ``images`` array."""
    assets: list[VisualAsset] = []
    for image in images:
        row = coerce_object(image)
        file_name = str(row.get("file_name") or "")
        assets.append(
            VisualAsset(
                asset_id=str(row.get("id") or file_name),
                file_name=file_name,
                image_path_or_uri=(
                    string_or_none(row.get("coco_url"))
                    or string_or_none(row.get("path"))
                    or resolve_image_path(file_name, image_root)
                ),
                width=int(row.get("width") or 0),
                height=int(row.get("height") or 0),
                split=string_or_none(row.get("split")),
                source_asset_id=str(row.get("id") or file_name),
            )
        )
    return assets


def build_categories(
    categories: list[object],
    *,
    category_frequency_key: str | None = None,
) -> list[VisualCategory]:
    """Build ``VisualCategory`` records from a COCO-style ``categories`` array."""
    values: list[VisualCategory] = []
    for category in categories:
        row = coerce_object(category)
        metadata: dict[str, object] = {}
        synonyms = row.get("synonyms")
        if isinstance(synonyms, list):
            metadata["synonyms"] = [str(item) for item in synonyms]
        values.append(
            VisualCategory(
                category_id=str(row.get("id") or row.get("name") or ""),
                name=str(row.get("name") or ""),
                supercategory=string_or_none(row.get("supercategory")),
                frequency_tier=(
                    string_or_none(row.get(category_frequency_key))
                    if category_frequency_key is not None
                    else None
                ),
                metadata=metadata,
            )
        )
    return values


def build_annotations(
    annotations: list[object],
    *,
    category_names: dict[str, str],
) -> list[VisualAnnotation]:
    """Build ``VisualAnnotation`` records from a COCO-style ``annotations`` array."""
    values: list[VisualAnnotation] = []
    for annotation in annotations:
        row = coerce_object(annotation)
        category_id = string_or_none(row.get("category_id"))
        segmentation = row.get("segmentation")
        values.append(
            VisualAnnotation(
                annotation_id=str(row.get("id")),
                asset_id=str(row.get("image_id")),
                category_id=category_id,
                category_name=category_names.get(category_id or ""),
                task_type=infer_task_type(row),
                bbox_xywh=float_list_or_none(row.get("bbox")),
                polygons=polygon_list(segmentation),
                rle=coerce_object(segmentation) if isinstance(segmentation, dict) else None,
                keypoints_xyv=float_list_or_none(row.get("keypoints")),
                area=float(row["area"]) if isinstance(row.get("area"), (int, float)) else None,
                iscrowd=(
                    bool(row["iscrowd"])
                    if isinstance(row.get("iscrowd"), (int, bool))
                    else None
                ),
                score=float(row["score"]) if isinstance(row.get("score"), (int, float)) else None,
                source_annotation_id=str(row.get("id")),
            )
        )
    return values


def infer_task_type(annotation: dict[str, object]) -> str:
    """Infer the annotation task type from the available geometry fields."""
    segmentation = annotation.get("segmentation")
    if float_list_or_none(annotation.get("keypoints")):
        return "keypoints"
    if isinstance(segmentation, dict) or polygon_list(segmentation):
        return "instance_segmentation"
    if float_list_or_none(annotation.get("bbox")):
        return "bbox"
    return "classification"
