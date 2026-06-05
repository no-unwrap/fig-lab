"""Import smoke test for the plotting stack."""

from __future__ import annotations

import importlib

MODULES = [
    "matplotlib",
    "seaborn",
    "bokeh",
    "altair",
    "plotnine",
    "plotly",
    "holoviews",
    "hvplot",
    "datashader",
    "panel",
    "lets_plot",
    "napari",
    "scienceplots",
]


def main() -> int:
    for module_name in MODULES:
        importlib.import_module(module_name)
        print(f"ok: {module_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
