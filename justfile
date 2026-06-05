set shell := ["/bin/zsh", "-lc"]

setup:
    @echo "Python dependencies are provided by the declarative workstation; no repo-local venv is required."
    @echo "PYTHONPATH=src python -m fig_lab.main --version"
    PYTHONPATH=src python -m fig_lab.main --version

lint:
    python -m ruff check .

test:
    python -m pytest -q

smoke:
    PYTHONPATH=src python -m fig_lab.main smoke
