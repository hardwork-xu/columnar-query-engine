# Engineering increment

Problem: the B vector pipeline constructs and applies a row mask in every segment even when a narrow predicate cannot possibly match it. Hypothesis: coarse segment summaries can eliminate most row work on ordered or clustered data while preserving exact counts and tolerance-equivalent sums.

Implementation: numeric lower/upper bounds and capped categorical membership summaries are constructed once with the table. The same table, query and output requirements are used in B and C; only `prune` differs. A failed may-match check skips the whole segment. The summaries are computed from owned validated arrays and never accepted from untrusted saved metadata.

The preregistered >=80% work reduction target passed at all three ordered sizes: 94.88%, 97.95%, 98.72%. Every B/C trial and optional native DuckDB reference agrees. Costs: summary construction, Python metadata, and per-segment checks. Shuffled selective workloads prune nothing and C is slower in each measured scale. Full scans also prune nothing. Timing noise can make either path slightly faster; no benefit is inferred from those small differences. High-cardinality categorical summaries intentionally fall back to scanning.

This reproduces an established database optimization in a small independently maintained engine. DuckDB already has statistics pruning; there is no novelty or upstream performance superiority claim. See raw trials and protocol in EXPERIMENTS.
