# Scope and preregistered acceptance

Recorded 2026-09-21 (Asia/Shanghai), before implementation.

SegmentLens independently implements a small DuckDB-inspired columnar execution subsystem: immutable column ingestion/persistence; batch selection vectors for conjunctive typed filters; grouped count/sum aggregation. Reference: duckdb/duckdb commit `7e1c37c0e96182c8f00843274043a0e7d2f0287e` (MIT), 41,601 stars / 3,812 forks at the 2026-09-21 live audit. This is an unofficial implementation, neither a fork nor a complete SQL database. No upstream source is copied. Reading source means this is not claimed to be a strict clean-room implementation.

B is the vectorized full segment scan. C adds conservative numeric min/max and bounded categorical membership summaries to skip impossible segments before selection/aggregation. DuckDB already provides statistics pruning; this is an engineering increment over our own B, not a novel algorithm or a claim to improve DuckDB.

Target fixed before tuning: at least 80% fewer predicate-evaluated rows on each ordered selective range workload of 10,000 / 50,000 / 200,000 rows, segment size 512; output counts exactly equal and sums within rtol=1e-10, atol=1e-10. Three repetitions after one warm-up; seed 20260921; single BLAS thread; alternate B/C order. Report all timings, including unfavorable random-order and unselective queries. This work metric is not physical disk I/O or RSS. Metadata construction and full load time are reported separately from query time. NumPy uses float64. Synthetic data only.

Boundary: finite float64 numeric columns and Unicode strings; no SQL parser, joins, updates, MVCC, network service, NULL semantics, parallel engine, or crash-safe database transactions. The in-memory table must fit RAM. Persistence uses non-pickle NPZ, loads fully and recomputes metadata; no disk skip claim. Native DuckDB 1.4.0 is an optional separately pinned correctness oracle, not a timing comparison against the source-study SHA.

Acceptance: reference aggregate parity, valid/invalid boundaries, read-only columns, serialization round-trip, conservative pruning for every supported predicate, CLI integration, reproducible raw result schema, wheel/sdist build. Docker is not available locally; CI must establish its actual status separately.
