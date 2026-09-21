# 上游分析

DuckDB 通过列式存储、向量和执行流水线解决进程内分析查询。固定研究快照为 [`7e1c37c0e96182c8f00843274043a0e7d2f0287e`](https://github.com/duckdb/duckdb/commit/7e1c37c0e96182c8f00843274043a0e7d2f0287e)。2026-09-21（Asia/Shanghai）GitHub API实时核验为41,601 Stars、3,812 Forks；观察到正式版本v1.5.5发布于2026-07-22。快照包含2026-09-21事务回退修复，近期实质代码活动在90天内。Stars仅为快照，不代表增长趋势。

实际阅读：[DataChunk](https://github.com/duckdb/duckdb/blob/7e1c37c0e96182c8f00843274043a0e7d2f0287e/src/common/types/data_chunk.cpp)、[选择向量](https://github.com/duckdb/duckdb/blob/7e1c37c0e96182c8f00843274043a0e7d2f0287e/src/include/duckdb/common/types/selection_vector.hpp)、[物理过滤](https://github.com/duckdb/duckdb/blob/7e1c37c0e96182c8f00843274043a0e7d2f0287e/src/execution/operator/filter/physical_filter.cpp)、[数值统计](https://github.com/duckdb/duckdb/blob/7e1c37c0e96182c8f00843274043a0e7d2f0287e/src/storage/statistics/numeric_stats.cpp)、[哈希聚合](https://github.com/duckdb/duckdb/blob/7e1c37c0e96182c8f00843274043a0e7d2f0287e/src/execution/operator/aggregate/physical_hash_aggregate.cpp)。过滤器使用SelectExpression生成选择向量并切片，统计模块为段提供保守边界。已阅读实际MIT[许可证](https://github.com/duckdb/duckdb/blob/7e1c37c0e96182c8f00843274043a0e7d2f0287e/LICENSE)。

本项目以Python/NumPy独立实现有限子系统，核心执行不调用DuckDB。未复制上游代码或数据；src/segmentlens模块与测试均在源码研究后针对本项目编写，不宣称严格clean-room。DuckDB已具有统计剪枝和完整优化器；min/max与有界类别摘要是相对本项目完整扫描B的工程增量，不宣称首创或上游没有该能力。实际运行的可选原生DuckDB 1.4.0仅用于正确性对照，与研究快照不同，不作上游速度比较。

唯一运行依赖NumPy采用BSD-3-Clause，其wheel内含另外许可的组件；未分发模型、外部数据或素材。参见[第三方清单](../../THIRD_PARTY.md)。
