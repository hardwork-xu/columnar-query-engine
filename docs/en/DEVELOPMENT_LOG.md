# Development log

The initial implementation entries below occurred on 2026-09-21, Asia/Shanghai. They describe one engineering session; subsequent dated sections record later work.

- Read pinned DuckDB source and MIT license. Execute `work/research/data/probe.py` outside the repository: native/scalar/segment outputs agree. Private orchestration paths and downloaded upstream source are not versioned here.
- `e85e1dc`: commit scope and preregistered target before core implementation.
- `6ac2e47`: add baseline owned columns, typed predicates, selection and grouped aggregation. `python -m pytest -q`: 15 passed.
- `8b8838e`: add min/max and categorical pruning. Tests expanded to scalar reference, boundary operators, no-match, fallback and unfavorable scans: 26 passed. `ruff check src tests`: passed.
- `67dc02f`: add CLI and complete paired experiment runner. CLI/persistence/schema integration checks: 30 passed.
- Run `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m segmentlens bench --output results/benchmark.json --oracle-duckdb`: all 54 trials and oracle comparisons passed. Ordered reduction target met; shuffled workloads revealed negative timing tradeoff.
- Add generated result tables, bilingual design/reproduction documents and packaging/CI configuration. Subsequent build and remote verification are recorded in release checks, not inferred from configuration files.
- Cross-review reproduced an invalid NPZ JSON header causing an uncaught AttributeError. Tightened archive schema validation and added malformed-header/CLI regressions. The report renderer now rejects failed/incomplete trials. These validation changes do not alter the measured successful core path; the preserved benchmark identifies its original source commit.

## 2026-10-13 — layout and evidence safety

- Reproduced the public `segment_size` reassignment failure: full scan returned count 2 / sum 201, while pruning returned no rows after a layout-only change. This was unsupported reconfiguration accepted silently, not an ordinary immutable-table query error.
- Replaced writable `segment_size` / `length` with read-only properties backed by private fields. Added assignment/deletion rejection, query preservation, save/load and explicit-rebuild regressions.
- Replaced the experiment runner’s final overwrite with exclusive creation, rejected dangling symlinks before work, and tested existing/racing destinations plus preservation of failed-run records.
- `python -m pytest -q`: 52 passed, including 14 new cases. No tolerance was relaxed. No formal performance experiment was run; old raw data remains unchanged and explicitly historical.
