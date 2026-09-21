# Experiments

Run `segmentlens-bec82c0d6994`, source commit `67dc02f2f459f77e92a80911ebe5704098ce4e7a` (clean working tree at measurement). [Raw JSON](../../results/benchmark.json) contains each of 54 paired trials, configuration, data hashes, source hash, UTC start/end, ingestion/save/load costs and status. Published measurements: Apple M1 Pro, 16 GiB, macOS 26.6.2 arm64, Python 3.12.2, NumPy 2.3.3. CPU only; BLAS thread variables all 1. Native correctness oracle: DuckDB 1.4.0 with one thread. It is neither the studied SHA nor an upstream speed measurement.

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
