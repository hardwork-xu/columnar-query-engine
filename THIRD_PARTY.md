# Sources and dependency licenses / 来源与依赖许可

- **DuckDB**: MIT, copyright Stichting DuckDB Foundation; studied at `7e1c37c0e96182c8f00843274043a0e7d2f0287e`. Source locations are in UPSTREAM_ANALYSIS. No code/files/snippets copied or modified into this repository. Conceptual influence: vectors, selection and conservative segment statistics. 非官方机制复现，未复制上游源码。
- **Own implementation / 自主实现**: all files under `src/segmentlens/`, tests, experiment runner and documentation are independently written for this project following source inspection. This does not establish strict clean-room provenance. 源码阅读后独立编写，不作严格clean-room声明。
- **NumPy 2.3.3**: BSD-3-Clause. Installed wheel distribution contains its own third-party notices (including platform-dependent BLAS and runtime components). This repository distributes dependency specifications, not bundled binary wheels. NumPy executes array primitives; SegmentLens implements query validation, segmentation, pruning, traversal, state and result reduction.
- Optional **DuckDB 1.4.0** MIT wheel: correctness oracle only, not imported by the core package and not redistributed. This is a different fixed release from the source-study commit.
- Development tools: pytest MIT; setuptools MIT; wheel MIT; build MIT; ruff MIT; packaging Apache-2.0/BSD-2-Clause; pyproject-hooks MIT; iniconfig MIT; pluggy MIT; Pygments BSD-2-Clause. Their original distributions carry their licenses.
- Synthetic input generator only; no third-party models, private data, external datasets or visual assets. 仅合成输入，无模型、私人数据或外部数据集。

No additional source-use restrictions were found in the examined DuckDB MIT file. Dependency binary redistribution would require reviewing the target wheel's notices. 未把第三方许可重写为本项目MIT。
