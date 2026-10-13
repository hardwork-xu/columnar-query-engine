# Experiments

**Measurement/source boundary (2026-10-13).** Each table and raw file below is tied to its own source commit; the original historical evidence is preserved. The current code rejects live layout reassignment and creates result files exclusively, including when a competing file or symlink appears after preflight. Ordinary experiment exceptions still produce a `failed` record when the destination is available; an occupied path is never replaced. Exclusive creation is not an atomic/durable publication guarantee if the writer crashes. Read-only property access changes the query hot path. A separate repaired-source run has now measured B/C timings and setup costs; its results are shown before the unchanged historical record. Functional result-schema tests are not performance evidence.

## Repair measurement — 2026-10-13

Run `segmentlens-f0eea47a2116` started at `2026-10-13T04:06:58.477380+00:00` and finished at `2026-10-13T04:06:59.435200+00:00`. It measured clean commit `00c50b3c9413f2894909bcf2d8fa9ff2863492f6`; package SHA256 is `2e132bf70f993a54899c90af9444ac4c8a9edfb9334c46e8d1899b2c88dfd180`. [Raw JSON](../../results/layout-repair-20261013.json) SHA256: `942c1e268718b1d5fa0d3287c1b101328133aef71ac7594cc9fa7dca00bb5b62`.

Environment recorded by this run: Darwin 25.6.0 arm64, 10 logical CPUs, Python 3.12.2, NumPy 2.3.3; OMP/OPENBLAS/VECLIB thread variables all 1. The protocol/configuration is identical to the historical run described below: three scales, three workloads, one warm-up per mode, three alternating B/C repeats, 54 trial records. Query-only medians exclude separately recorded ingestion, save and load costs. Each of nine cases has a passed DuckDB 1.4.0 single-thread correctness comparison; DuckDB timings were not measured.

<!-- REPAIR_RESULTS_START -->
| Rows / 行数 | Workload / 负载 | B ms | C ms | Fewer evaluated rows / 求值行减少 |
|---:|---|---:|---:|---:|
| 10000 | ordered_selective | 0.240 | 0.047 | 94.88% |
| 10000 | shuffled_selective | 0.314 | 0.326 | 0.00% |
| 10000 | ordered_all | 0.898 | 0.931 | 0.00% |
| 50000 | ordered_selective | 1.141 | 0.155 | 97.95% |
| 50000 | shuffled_selective | 1.578 | 1.736 | 0.00% |
| 50000 | ordered_all | 4.813 | 5.035 | 0.00% |
| 200000 | ordered_selective | 4.613 | 0.566 | 98.72% |
| 200000 | shuffled_selective | 6.488 | 6.488 | 0.00% |
| 200000 | ordered_all | 19.187 | 19.409 | 0.00% |
<!-- REPAIR_RESULTS_END -->

All three ordered selective targets passed: C evaluates 512/1,024/2,560 rows at 10k/50k/200k, with reductions 94.88%/97.952%/98.72%. Counts match exactly; recorded sums satisfy unchanged rtol/atol 1e-10. All 54 B/C trial checks and nine oracle checks passed; failures are an empty list. Independent untimed review reconstructed input hashes, grouped references and segment work counters from the saved seed/configuration. That review is validation of the saved run, not another experiment.

All six zero-pruning workloads remain in the table. Shuffled C time is +3.88%, +10.00%, +0.0045% relative to B; broad-scan C time is +3.71%, +4.59%, +1.16%. The 200k shuffled median difference is about 0.000292 ms and rounds away in the table; three repeats do not establish its practical or statistical significance. No confidence interval or cross-machine generality is established. This rerun validates the repaired engineering implementation under this synthetic protocol; it does not establish research maturity, upstream superiority, or a causal speed change attributable to the repair between dated runs.

Generate the table from the committed raw file; the next commands optionally perform a new run at a fresh path (existing outputs are never replaced):

```sh
python -m segmentlens report results/layout-repair-20261013.json
python -m pip install duckdb==1.4.0
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m segmentlens bench --output results/layout-repair-local.json --oracle-duckdb
python -m segmentlens report results/layout-repair-local.json
```

## Historical measurement — original implementation

Run `segmentlens-bec82c0d6994`, source commit `67dc02f2f459f77e92a80911ebe5704098ce4e7a` (clean working tree at measurement). [Raw JSON](../../results/benchmark.json) contains each of 54 individual mode trials (27 B/C pairs), configuration, data hashes, source hash, UTC start/end, ingestion/save/load costs and status. Published measurements: Apple M1 Pro, 16 GiB, macOS 26.6.2 arm64, Python 3.12.2, NumPy 2.3.3. CPU only; BLAS thread variables all 1. Native correctness oracle: DuckDB 1.4.0 with one thread. It is neither the studied SHA nor an upstream speed measurement.

Fixed seed20260921, sizes10k/50k/200k, segment512, 4 groups, float64. Narrow range is [0.45N,0.46N); ordered and randomly shuffled key layouts share the query semantics. Broad range is [0,N). One warm-up per mode then three repeats with alternating B/C order. Measurement starts before input-query validation and includes filtering and aggregation; setup and loading are separately timed. No external data, models, network or device transfers enter the query.

Primary target: >=80% fewer predicate-evaluated rows on ordered selective workloads, exact count equality and sums rtol/atol1e-10. Rows evaluated are an algorithmic work counter, not bytes read, memory or end-to-end throughput. Target was committed before implementation. The experiment also compares serialization round-trips and native DuckDB output. All assertions passed; no failed formal trials occurred. Small-scale experiment-schema tests do not constitute additional benchmark evidence.

| Rows / 行数 | Workload / 负载 | B ms | C ms | Fewer evaluated rows / 求值行减少 |
|---:|---|---:|---:|---:|
| 10000 | ordered_selective | 0.231 | 0.046 | 94.88% |
| 10000 | shuffled_selective | 0.303 | 0.319 | 0.00% |
| 10000 | ordered_all | 1.148 | 1.047 | 0.00% |
| 50000 | ordered_selective | 1.128 | 0.156 | 97.95% |
| 50000 | shuffled_selective | 1.491 | 1.532 | 0.00% |
| 50000 | ordered_all | 5.292 | 5.290 | 0.00% |
| 200000 | ordered_selective | 5.329 | 0.595 | 98.72% |
| 200000 | shuffled_selective | 6.605 | 6.933 | 0.00% |
| 200000 | ordered_all | 21.455 | 21.165 | 0.00% |

Time is median milliseconds; all individual values and zero-pruning negative results are retained. Do not extrapolate these small synthetic CPU results to production database workloads.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m segmentlens bench --output results/local-benchmark.json
python -m segmentlens report results/local-benchmark.json
# Optional independent oracle:
python -m pip install duckdb==1.4.0
# Use a fresh result filename; add --oracle-duckdb to the benchmark command.
```

`report` derives both README tables from JSON. The archive writer refuses to overwrite results. For supported-platform Docker/CI status, inspect the actual workflow run; Docker was unavailable on the local host at measurement.
