"""Canonical source-kind identifiers shared across readers and specs."""

from __future__ import annotations

# Dataset source kinds
PUBLISHED_RELEASE_BUNDLE = "published_release_bundle"
COCO = "coco"
LVIS = "lvis"
PASCAL_VOC = "pascal_voc"
SUPPORTED_DATASET_SOURCE_KINDS = {
    PUBLISHED_RELEASE_BUNDLE,
    COCO,
    LVIS,
    PASCAL_VOC,
}

# Experiment source kinds
STANDALONE_METRIC_TABLE = "standalone_metric_table"
REPR_LAB_RUN_DIRECTORY = "repr_lab_run_directory"
SUPPORTED_EXPERIMENT_SOURCE_KINDS = {
    STANDALONE_METRIC_TABLE,
    REPR_LAB_RUN_DIRECTORY,
}
