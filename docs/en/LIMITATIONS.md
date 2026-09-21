# Limitations

Experimental v0.1.0, CPU only. No SQL parser, joins, concurrent mutation, transactions, durable crash recovery, spill, distributed execution or production deployment. No NULL/NaN/Inf support. Finite float64 sums are order-dependent within stated tolerances; extreme finite inputs can overflow and are rejected. Integer magnitudes above 2^53 are unsupported.

Full arrays are resident; NPZ loads all data. Segment summaries and NumPy temporary buffers consume additional memory. High cardinality and shuffled data can defeat pruning; broad queries can be slower with C. Categorical summaries cap at256 values. Input copying and metadata building are additional ingestion cost, explicitly measured.

The fixture is synthetic and small; no user dataset or industry benchmark is evaluated. DuckDB 1.4.0 correctness runs are a separate version from the studied SHA. There is no upstream timing comparison. Local Docker execution was not available; a passing actual CI Docker job, if present, validates Linux CPU only. It would not establish Metal/CUDA support.

NPZ files are expected to be trusted and reasonably sized. `allow_pickle=False` avoids pickle code execution but is not an archive resource-limit sandbox. Save refuses overwrite but is not atomic database commit/recovery. The read-only array API is a programming contract rather than a hostile-code security boundary.
