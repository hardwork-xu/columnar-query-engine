# Design and API

`Table(columns, segment_size=512)` owns copies of one-dimensional numeric/Unicode arrays. Numeric data uses finite float64; integers outside the exactly representable ±2^53 range are rejected. All columns have equal length and exposed views are read-only. Empty tables are valid. This protects ordinary accidental mutation, not hostile Python code manipulating private storage.

`Predicate(column, op, value)` supports numeric `eq/lt/le/gt/ge/between/in`, and string `eq/in`. `between` is inclusive. `Query(measure, group_by, predicates=())` requests grouped count and sum; conditions combine with AND. `Query.from_dict` rejects unknown fields. `execute(table, query, prune=False)` selects B; `prune=True` selects C and is the default. `Result.rows` is a sorted list of key/count/sum objects; `Result.stats` explains total/skipped segments and evaluated/matching rows. Empty results are `[]`; sums that overflow are rejected.

For each segment, C evaluates conservative metadata before allocating a Boolean mask. Numeric intervals may overlap even when no row matches; this only causes extra scanning. Categorical sets are stored only up to 256 distinct values; higher cardinality falls back to scanning. Selected row indexes then gather the measure and grouping columns. NumPy unique/bincount produces partial groups, merged by key into the result.

With N rows, C columns, batch length b and G global groups: owned data O(NC), numeric summaries O(NC/b), bounded string summaries O(256NC/b) worst case; masks/indexes O(b), output state O(G). Local unique costs O(b log b). Pruning can eliminate batches but its worst case remains a full scan plus metadata checks. No parallel worker state exists.

`Table.save(path)` refuses to overwrite an existing `.npz`; `Table.load(path)` disables pickle, validates all data and rebuilds summaries. Persistence is a trusted local file convenience, not a crash-safe transaction system or adversarial archive sandbox. Opening loads all columns. Query timing excludes table construction and NPZ load, each recorded separately. Context managers close archives/files; temporary benchmark directories are removed.
