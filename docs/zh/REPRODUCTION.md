# 复现过程与能力映射

1. 阅读固定chunk、选择向量、过滤、统计源码及MIT许可。
2. 可行性验证：真实运行4,096行区间聚合，NumPy/原生DuckDB 1.4.0标量结果0.8130929838507273与分段结果0.8130929838507281在误差范围内一致，仅256行需要求值。
3. 先提交范围目标（e85e1dc），再实现B（6ac2e47）、加入C（8b8838e）。
4. 验证标量参考、持久化、保守边界，提交实验程序（67dc02f）。
5. 运行预定配对实验，全部试次保存在[JSON](../../results/benchmark.json)。

| 固定上游 `7e1c37c0e961` 行为 | 上游源码 | 本项目模块/状态 | 验证 | 差异 |
|---|---|---|---|---|
| 列批次 | src/common/types/data_chunk.cpp | engine.Table，已实现 | test_baseline_and_roundtrip | 全表内存常驻、NPZ保存 |
| 选择向量 | src/include/duckdb/common/types/selection_vector.hpp | _mask、execute，已实现 | test_conservative_pruning_matches_scalar | NumPy索引数组，仅合取 |
| 过滤执行 | src/execution/operator/filter/physical_filter.cpp | _validated、_mask，已实现 | 类型与非法输入测试 | 无SQL优化器、NULL |
| 统计剪枝 | src/storage/statistics/numeric_stats.cpp | _possible、_summaries，已实现 | test_pruning_and_unfavorable_cases | 数值边界及最多256项类别集合 |
| 分组聚合 | src/execution/operator/aggregate/physical_hash_aggregate.cpp | execute，已实现 | 标量及原生参考 | 段内NumPy归约、段间Python字典 |

初次Python HTTPS源码下载遇到本机证书验证失败，随后改用正常认证的GitHub contents API读取，未关闭TLS验证。正式实验全部通过，无挑选有利试次；无序数据没有工作量收益，C通常稍慢。
