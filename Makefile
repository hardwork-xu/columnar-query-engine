PYTHON ?= python
.PHONY: install demo test lint bench report build
install:
	$(PYTHON) -m pip install -r requirements-dev.txt
	$(PYTHON) -m pip install -e .
demo:
	$(PYTHON) -m segmentlens demo
test:
	$(PYTHON) -m pytest -q
lint:
	$(PYTHON) -m ruff check src tests
bench:
	OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 $(PYTHON) -m segmentlens bench --output results/local-benchmark.json
report:
	$(PYTHON) -m segmentlens report results/benchmark.json
build:
	$(PYTHON) -m build --no-isolation
