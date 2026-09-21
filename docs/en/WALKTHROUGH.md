# Code walkthrough

Read in this order: `tests/test_engine.py` (contract) -> `engine.Table` (owned data and summaries) -> `_validated` -> `_possible` (one-sided conservative bounds) -> `_mask` and `execute` (selection and reduction) -> `benchmark.run_benchmark` -> raw trials.

CLI entry `__main__` -> `cli.main` -> `Table`/`Query` -> `execute`. Invariant: a summary returning false implies no matching row; an uncertain summary must return true. Invariant: B/C differ only by whole-segment elimination, never by approximate output or a changed query. Put a debugger at `_possible` with the `test_pruning_and_unfavorable_cases` fixture: nine of ten segments are eliminated, while the scalar oracle remains exact.

To extend an operator, update typed validation, row mask and conservative summary together, then use independent scalar tests including equality at extrema. An unsupported summary should return true. To add nullable columns, first define three-valued Boolean semantics and null-aware count/sum; substituting NaN without these rules is incorrect. API parameters/outputs and Chinese explanations are documented in the matching DESIGN page.
