# Docs Index

Use this folder for:

- architecture and visualization-pipeline references
- setup, validation, and plotting-stack runbooks
- runtime notes for reader, figure-spec, and export seams

Active runtime note:

- `src/fig_lab/` is the live Python runtime tree
- `inspect-release` is the public bundle-reader surface
- `inspect-dataset` is the public raw-dataset reader surface
- `render-figure` is the public figure/export surface for static and
  interactive outputs
- `artifacts/` is the output evidence surface for figures, dashboards,
  manifests, and review exports

Validation note:

- the default validation commands are `python -m fig_lab.main smoke`,
  `python -m fig_lab.smoke`, and `python -m pytest -q`
- `docs/runbooks.md` is the detailed setup and validation guide

Current high-value docs:

- `docs/architecture.md`
- `docs/runbooks.md`
