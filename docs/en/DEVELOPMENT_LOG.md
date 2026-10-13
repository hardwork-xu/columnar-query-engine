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
- `python -m pytest -q`: 52 passed, including 14 new cases. No tolerance was relaxed. No formal performance experiment had run at this initial repair checkpoint; old raw data remained unchanged and explicitly historical. The later same-day run is recorded below.


## 2026-10-13 — repaired-source measurement

- At clean commit `00c50b3c9413f2894909bcf2d8fa9ff2863492f6`, ran `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m segmentlens bench --output results/layout-repair-20261013.json --oracle-duckdb`. Run `segmentlens-f0eea47a2116` exited successfully: 9 cases / 54 trials, three ordered row-work targets and nine DuckDB 1.4.0 correctness comparisons passed. This measured repaired runtime source, not a claim of new research maturity.
- Independently checked saved source/data hashes, unchanged protocol, reference aggregates and all trial counters without running another benchmark. All six zero-pruning cases and their timing costs are retained. The 200k shuffled timing difference is negligible at the reported precision.
- Used `python -m segmentlens report results/layout-repair-20261013.json` to generate the same new table for both READMEs and both experiment documents. Kept the original raw file and table byte-for-byte; labels separate the two measurement commits. Local Markdown links, bilingual new command blocks and table-to-raw equality passed. No runtime code or protocol changed in this documentation step.
