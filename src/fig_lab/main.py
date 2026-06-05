"""CLI entrypoint for fig-lab.

Dispatches to subcommands for artifact inspection, figure rendering, and
plotting-stack smoke testing.
"""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from fig_lab import __version__
from fig_lab._source_kinds import SUPPORTED_DATASET_SOURCE_KINDS, SUPPORTED_EXPERIMENT_SOURCE_KINDS
from fig_lab.dataset_reader import load_dataset_bundle
from fig_lab.experiment_reader import load_experiment_bundle
from fig_lab.figure_rendering import render_figure_from_spec_path
from fig_lab.release_reader import load_published_release_bundle


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fig-lab",
        description=(
            "Figure generation and visualization framework for published "
            "dataset and experiment artifacts."
        ),
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the fig-lab package version and exit.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        "smoke",
        help="Import the plotting stack and emit one line per successfully imported module.",
    )
    inspect_release = subparsers.add_parser(
        "inspect-release",
        help="Read a published release bundle into the canonical figure-facing dataset view.",
    )
    inspect_release.add_argument(
        "--bundle-dir",
        required=True,
        help="Path to the published release bundle directory.",
    )
    inspect_dataset = subparsers.add_parser(
        "inspect-dataset",
        help="Read a raw dataset source into the canonical figure-facing dataset view.",
    )
    inspect_dataset.add_argument(
        "--source-kind",
        required=True,
        choices=sorted(SUPPORTED_DATASET_SOURCE_KINDS),
        help="Dataset source kind: published_release_bundle, coco, lvis, or pascal_voc.",
    )
    inspect_dataset.add_argument(
        "--source-path",
        required=True,
        help="Path to the dataset source file or directory.",
    )
    inspect_experiment = subparsers.add_parser(
        "inspect-experiment",
        help="Read an experiment source into the canonical figure-facing metric table view.",
    )
    inspect_experiment.add_argument(
        "--source-kind",
        required=True,
        choices=sorted(SUPPORTED_EXPERIMENT_SOURCE_KINDS),
        help=(
            "Experiment source kind: standalone_metric_table or the bounded "
            "repr_lab_run_directory contract."
        ),
    )
    inspect_experiment.add_argument(
        "--source-path",
        required=True,
        help="Path to the experiment source file or directory.",
    )
    render_figure = subparsers.add_parser(
        "render-figure",
        help="Load a figure spec and emit a figure artifact plus export manifest.",
    )
    render_figure.add_argument(
        "--spec",
        required=True,
        help="Path to the JSON figure spec file.",
    )
    render_figure.add_argument(
        "--output-dir",
        required=True,
        help="Directory where the figure artifact and export manifest will be written.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"fig-lab {__version__}")
        return 0

    if args.command == "smoke":
        from fig_lab.smoke import main as smoke_main

        return smoke_main()

    if args.command == "inspect-release":
        bundle = load_published_release_bundle(args.bundle_dir)
        print(json.dumps(bundle.to_summary_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "inspect-dataset":
        bundle = load_dataset_bundle(args.source_kind, args.source_path)
        print(json.dumps(bundle.to_summary_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "inspect-experiment":
        bundle = load_experiment_bundle(args.source_kind, args.source_path)
        print(json.dumps(bundle.to_summary_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "render-figure":
        payload = render_figure_from_spec_path(args.spec, args.output_dir)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
