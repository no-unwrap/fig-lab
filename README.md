# fig-lab

Visualization and figure-production framework for artifact-backed research
outputs.

A framework-oriented repository for turning stable dataset or experiment
artifacts into truthful visual products, repeatable figure specs, and
exportable review bundles.

## Design Intent

`fig-lab` is designed as a research instrument, not a notebook gallery.

It is meant to support:

- normalized readers before plotting backends enter the picture
- renderer-agnostic figure specifications
- export manifests that preserve artifact provenance
- static, interactive, and qualitative review surfaces from one coherent
  runtime

Key principle:

- readers normalize once, figure specs stay stable, and plotting backends adapt
  around that shared contract

## Repo Map

- `src/fig_lab/`: active Python runtime for readers, contracts, CLI entrypoints,
  and smoke surfaces
- `tests/`: runtime and CLI validation surface
- `artifacts/`: persisted output surface for figures, dashboards, manifests,
  and review exports
- `docs/README.md`: docs index
- `docs/architecture.md`: runtime map and plotting-stack posture
- `docs/runbooks.md`: setup, validation, and runtime reference

## 60-Second Setup

Use Python `3.13` for now. The `napari` dependency chain is not yet fully
compatible with Python `3.14`.

1. Use Python `3.13` from an environment that already contains the repo
dependencies. On declaratively managed workstations, no repo-local `.venv`
is required.

```bash
just setup
```

2. Check the public CLI surface.

```bash
PYTHONPATH=src python -m fig_lab.main --version
PYTHONPATH=src python -m fig_lab.main inspect-release --bundle-dir /path/to/release-bundle
PYTHONPATH=src python -m fig_lab.main inspect-dataset --source-kind coco --source-path /path/to/annotations.json
PYTHONPATH=src python -m fig_lab.main inspect-experiment --source-kind repr_lab_run_directory --source-path /path/to/repr-run
PYTHONPATH=src python -m fig_lab.main render-figure --spec /path/to/spec.json --output-dir artifacts/demo
```

3. Run the baseline validation passes.

```bash
PYTHONPATH=src python -m fig_lab.main smoke
PYTHONPATH=src python -m fig_lab.smoke
python -m pytest -q
```

## How It Works

```text
Artifact Reader -> Normalized Dataset View -> Figure Spec -> Renderer -> Export Manifest
```

- readers parse published release bundles first and fall back to bounded raw
  inputs only when a release bundle is not the right surface for the task
- raw `COCO`, `LVIS`, and `PASCAL VOC` readers now converge on the same
  dataset-facing contract as published release bundles
- contracts keep figure-facing data stable before renderer selection
- renderers emit static, interactive, or review-oriented outputs
- export surfaces preserve provenance back to the source artifacts

## Current Runtime Surfaces

- a public `inspect-release` CLI for release-bundle inspection
- a public `inspect-dataset` CLI for raw `COCO`, `LVIS`, and `PASCAL VOC`
  dataset inspection when bounded local visualization or adapter work needs a
  raw source
- a public `inspect-experiment` CLI for standalone metric tables and
  manifest-backed `repr-lab` run directories that satisfy the bounded public
  run-directory contract
- a public `render-figure` CLI that writes PNG, SVG, PDF, or HTML outputs plus
  an export manifest from a JSON figure spec
- a plotting-stack smoke path that validates the current dependency surface
- normalized contracts in `src/fig_lab/contracts.py`
- an artifact surface under `artifacts/` for exported figures and review bundles

## Current Focus

- expand figure-spec coverage beyond the current bar-oriented views while
  keeping output selection downstream of normalized records
- deepen experiment result coverage on top of the landed contract-aware
  `repr-lab` run-directory reader

## Safety Posture

- keep visual encodings truthful to the source artifacts
- preserve provenance in manifests and exported outputs
- keep renderer selection downstream of normalized records
- treat historical outputs as additive and auditable rather than mutable

## Docs Map

- `docs/README.md`: docs index
- `docs/architecture.md`: architecture, plotting-stack posture, and runtime
  overview
- `docs/runbooks.md`: bootstrap, validation, and runtime reference
- `artifacts/README.md`: artifact-output guidance

## License

This project is licensed under the MIT License. See `LICENSE` for the full
text.
