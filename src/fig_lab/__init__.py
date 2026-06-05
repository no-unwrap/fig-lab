"""fig-lab: visualization and figure-production framework for artifact-backed research outputs."""

from fig_lab._source_kinds import (
    COCO,
    LVIS,
    PASCAL_VOC,
    PUBLISHED_RELEASE_BUNDLE,
    REPR_LAB_RUN_DIRECTORY,
    STANDALONE_METRIC_TABLE,
)
from fig_lab.contracts import (
    DatasetView,
    FigureInputBundle,
    MetricRecord,
    MetricTable,
    VisualAnnotation,
    VisualAsset,
    VisualCategory,
    VisualSceneRating,
)
from fig_lab.dataset_reader import (
    load_coco_dataset,
    load_dataset_bundle,
    load_lvis_dataset,
    load_pascal_voc_dataset,
)
from fig_lab.experiment_reader import (
    load_experiment_bundle,
    load_repr_lab_run_directory,
)
from fig_lab.figure_rendering import render_figure, render_figure_from_spec_path
from fig_lab.figure_spec import load_figure_spec
from fig_lab.metric_reader import load_metric_table_bundle
from fig_lab.release_reader import load_label_lab_release_bundle, load_published_release_bundle

__version__ = "0.1.0"

__all__ = [
    "COCO",
    "LVIS",
    "PASCAL_VOC",
    "PUBLISHED_RELEASE_BUNDLE",
    "REPR_LAB_RUN_DIRECTORY",
    "STANDALONE_METRIC_TABLE",
    "DatasetView",
    "FigureInputBundle",
    "MetricRecord",
    "MetricTable",
    "VisualAnnotation",
    "VisualAsset",
    "VisualCategory",
    "VisualSceneRating",
    "__version__",
    "load_coco_dataset",
    "load_dataset_bundle",
    "load_experiment_bundle",
    "load_figure_spec",
    "load_label_lab_release_bundle",
    "load_lvis_dataset",
    "load_metric_table_bundle",
    "load_pascal_voc_dataset",
    "load_published_release_bundle",
    "load_repr_lab_run_directory",
    "render_figure",
    "render_figure_from_spec_path",
]
