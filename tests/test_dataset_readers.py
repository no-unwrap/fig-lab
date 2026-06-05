"""Error-path and standalone reader tests for dataset sources."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import write_pascal_voc_dataset, write_raw_lvis_dataset

from fig_lab.dataset_reader import (
    load_dataset_bundle,
    load_lvis_dataset,
    load_pascal_voc_dataset,
)


def test_load_dataset_bundle_rejects_unsupported_source_kind(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported dataset source_kind"):
        load_dataset_bundle("unknown_format", tmp_path / "fake.json")


def test_load_pascal_voc_raises_on_empty_directory(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(ValueError, match="no Pascal VOC annotation XML files"):
        load_pascal_voc_dataset(empty_dir)


def test_load_pascal_voc_raises_on_invalid_bbox(tmp_path: Path) -> None:
    annotations_dir = tmp_path / "Annotations"
    annotations_dir.mkdir(parents=True)
    (annotations_dir / "bad.xml").write_text(
        "\n".join([
            "<annotation>",
            "  <filename>bad.jpg</filename>",
            "  <size><width>100</width><height>100</height><depth>3</depth></size>",
            "  <object>",
            "    <name>obj</name>",
            "    <bndbox>",
            "      <xmin>200</xmin>",
            "      <ymin>100</ymin>",
            "      <xmax>100</xmax>",
            "      <ymax>200</ymax>",
            "    </bndbox>",
            "  </object>",
            "</annotation>",
        ]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="invalid Pascal VOC bbox extents"):
        load_pascal_voc_dataset(tmp_path)


def test_load_lvis_preserves_frequency_tier(tmp_path: Path) -> None:
    dataset_path = tmp_path / "lvis.json"
    write_raw_lvis_dataset(dataset_path)

    bundle = load_lvis_dataset(dataset_path)

    assert bundle.dataset_view is not None
    assert bundle.dataset_view.categories[0].frequency_tier == "rare"


def test_load_lvis_returns_correct_source_kind(tmp_path: Path) -> None:
    dataset_path = tmp_path / "lvis.json"
    write_raw_lvis_dataset(dataset_path)

    bundle = load_lvis_dataset(dataset_path)

    assert bundle.dataset_view is not None
    assert bundle.dataset_view.source_kind == "lvis"


def test_load_pascal_voc_builds_correct_view(tmp_path: Path) -> None:
    dataset_root = tmp_path / "voc"
    write_pascal_voc_dataset(dataset_root)

    bundle = load_pascal_voc_dataset(dataset_root)

    assert bundle.dataset_view is not None
    assert bundle.dataset_view.source_kind == "pascal_voc"
    assert bundle.dataset_view.task_types == ["bbox"]
    assert len(bundle.dataset_view.assets) == 1
    assert len(bundle.dataset_view.annotations) == 1
    annotation = bundle.dataset_view.annotations[0]
    assert annotation.category_name == "signal-object"
    assert annotation.bbox_xywh is not None
    assert annotation.bbox_xywh[2] > 0 and annotation.bbox_xywh[3] > 0


def test_load_pascal_voc_single_file_mode(tmp_path: Path) -> None:
    xml_path = tmp_path / "single.xml"
    xml_path.write_text(
        "\n".join([
            "<annotation>",
            "  <filename>img.jpg</filename>",
            "  <size><width>320</width><height>240</height><depth>3</depth></size>",
            "  <object>",
            "    <name>car</name>",
            "    <bndbox>",
            "      <xmin>10</xmin>",
            "      <ymin>20</ymin>",
            "      <xmax>110</xmax>",
            "      <ymax>120</ymax>",
            "    </bndbox>",
            "  </object>",
            "</annotation>",
        ]),
        encoding="utf-8",
    )

    bundle = load_pascal_voc_dataset(xml_path)

    assert bundle.dataset_view is not None
    assert len(bundle.dataset_view.annotations) == 1
    assert bundle.dataset_view.annotations[0].category_name == "car"
