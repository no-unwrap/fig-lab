# Architecture

## Intent

`fig-lab` is a visualization layer for research artifacts.

It should turn stable input artifacts into truthful, reusable visual products with clear figure specifications, reader logic, and exportable outputs.

The immediate data posture is `COCO`-first for dataset visualization, with explicit reader paths for `LVIS` and `PASCAL VOC`.

## Repository Layers

### Runtime

`src/fig_lab/` is the active Python runtime. The current runtime keeps the package importable, exposes a public CLI, provides a plotting-stack smoke surface, includes contract-aware dataset readers for published release bundles plus raw `COCO`, `LVIS`, and `PASCAL VOC` sources, includes experiment readers for standalone metric tables plus manifest-backed `repr-lab` run directories, and includes a renderer-agnostic figure-spec plus export-manifest path for `matplotlib` static outputs and `plotly` HTML outputs.

### Artifacts

`artifacts/` is the output surface for:
- figure manifests
- exported static figures
- dashboard bundles
- qualitative review exports
- visual QA sheets and contact mosaics

### Runtime Shape

`fig-lab` focuses on figure generation, dashboards, and qualitative
visualization outputs.

The runtime uses:
- stable dataset or experiment artifacts as inputs
- normalized figure-facing records before renderer selection

## Plotting Stack Direction

The plotting stack should be treated as a layered toolkit, not a bag of interchangeable libraries.

Static and publication-first direction:
- `matplotlib`
- `seaborn`
- `plotnine`
- `SciencePlots`

Interactive and dashboard direction:
- `altair`
- `plotly`
- `bokeh`
- `panel`

Large-scale or high-density direction:
- `holoviews`
- `hvplot`
- `datashader`

Qualitative image and overlay review direction:
- `napari`

## Current Architectural Posture

The runtime is intentionally small.

The repository is still early in its runtime buildout, but the key architectural pattern is now explicit on disk:

- dataset release bundles are the preferred dataset ingress when available and
  normalize into a canonical `DatasetView`
- raw `COCO`, `LVIS`, and `PASCAL VOC` datasets also normalize into that same
  `DatasetView` for bounded local inspection and adapter work
- standalone experiment metrics normalize into a `MetricTable`
- bounded contract-aware `repr-lab` run directories also normalize into that
  same `MetricTable`
- JSON figure specs remain backend-agnostic
- renderer selection stays behind the normalized record layer, with
  `matplotlib` handling static PNG/SVG/PDF exports and `plotly` handling HTML
  outputs
- export manifests preserve provenance back to the input bundle or metric table
