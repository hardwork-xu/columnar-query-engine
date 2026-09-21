# Reproduction and capability mapping

1. Inspect the fixed chunk/selection/filter/statistics source and MIT license.
2. Feasibility: execute a 4,096-row range sum with NumPy and DuckDB 1.4.0. The scalar sum 0.8130929838507273 and segment sum 0.8130929838507281 agree within floating tolerance; 256 rows need evaluation.
3. Commit the scope and target (`e85e1dc`), implement B (`6ac2e47`), then add C (`8b8838e`).
4. Verify scalar reference, persistence and conservative bounds; commit the experiment runner (`67dc02f`).
5. Execute the registered paired experiment and preserve every trial in [JSON](../../results/benchmark.json).

| Upstream behavior at `7e1c37c0e961` | Upstream path | Our module/status | Verification | Difference |
|---|---|---|---|---|
| Column chunks | `src/common/types/data_chunk.cpp` | `engine.Table`, implemented | `test_baseline_and_roundtrip` | Entire table resident; NPZ persistence |
| Selection vectors | `src/include/duckdb/common/types/selection_vector.hpp` | `_mask`, `execute`, implemented | `test_conservative_pruning_matches_scalar` | NumPy index arrays; AND only |
| Predicate filtering | `src/execution/operator/filter/physical_filter.cpp` | `_validated`, `_mask`, implemented | typed invalid/edge tests | No SQL optimizer or NULL |
| Statistics pruning | `src/storage/statistics/numeric_stats.cpp` | `_possible`, `_summaries`, implemented | `test_pruning_and_unfavorable_cases` | Python numeric pairs plus <=256 categorical set |
| Group aggregation | `src/execution/operator/aggregate/physical_hash_aggregate.cpp` | `execute`, implemented | scalar counts/sums and native oracle | NumPy local reduction and Python cross-segment dictionary |

A first direct Python HTTPS source download failed local certificate validation. Source inspection proceeded through authenticated GitHub contents API without disabling TLS verification. No code change was needed. Formal experiment results all passed; there is no hidden successful-only trial selection. Unfavorable unordered data has zero work reduction and usually slower C.
