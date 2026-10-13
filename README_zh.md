# 列式查询引擎 · Columnar Query Engine

仓库原名 `segmentlens`；包名及现有命令保持不变（`segmentlens`）。

[English](README.md)

用于研究选择性分析查询的小型CPU列式执行引擎：自有类型化数组、批次选择向量、分组count/sum聚合，以及用于跳过不可能命中段的保守数值/类别摘要。适合阅读查询引擎机制和开展可复现本地实验。

**范围：**独立、非官方复现DuckDB的向量扫描/过滤/聚合子系统，固定参考[`7e1c37c0e961`](https://github.com/duckdb/duckdb/commit/7e1c37c0e96182c8f00843274043a0e7d2f0287e)。未复制上游代码，不是完整SQL数据库。DuckDB已经具有统计剪枝；本项目贡献是可直接阅读的类型化流水线、有界摘要、验证及B/C实验，不宣称算法首创或超过上游。

```mermaid
flowchart LR
    A[Owned columns] --> B[Segment summaries]
    A --> C[Vector batches]
    B --> D{May match?}
    C --> D
    D -->|yes| E[Selection vector]
    D -->|no| F[Skip segment]
    E --> G[Grouped count and sum]
```

## 安装与运行

克隆[本仓库](https://github.com/hardwork-xu/columnar-query-engine)，在仓库根目录运行。要求Python3.11+、NumPy2.3.3；本地验证macOS arm64，Linux CPU以实际CI为准。无需密钥或模型下载。

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e .
python -m segmentlens demo
python -m pytest -q
ruff check src tests
python -m build --no-isolation
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m segmentlens bench --output results/local-benchmark.json
python -m segmentlens report results/local-benchmark.json
```

```python
from segmentlens import Table, Query, Predicate, execute
table = Table({"time": [1, 2, 3], "amount": [10, 20, 30], "kind": ["a", "a", "b"]}, segment_size=2)
query = Query("amount", "kind", (Predicate("time", "ge", 2),))
print(execute(table, query).rows)
# [{'key': 'a', 'count': 1, 'sum': 20.0}, {'key': 'b', 'count': 1, 'sum': 30.0}]
```

CLI帮助为双语。`query TABLE.npz QUERY.json --no-prune`使用完整扫描B；`execute(..., prune=True)`默认启用C。JSON字段包括measure、group_by及形如`{"column":"time","op":"ge","value":2}`的谓词列表。demo实际执行4,096行，两条路径均返回100个选中行，C仅求值256行。

## 实测结果

布局元数据（`segment_size`、`length`）只读，改变分段须重建 `Table`。2026-10-13 正确性修复同时阻止并发文件或符号链接导致实验结果被覆盖。下方分别列出修复后新测量与保留的历史测量；详见[实验边界](docs/zh/EXPERIMENTS.md)。

### 修复后测量 — 2026-10-13

运行 `segmentlens-f0eea47a2116` 测量布局修复后的干净源码 `00c50b3c9413f2894909bcf2d8fa9ff2863492f6`。环境：macOS arm64（Darwin 25.6.0）、Python 3.12.2、NumPy 2.3.3、CPU，三个记录的 BLAS 线程变量均为1。沿用原协议：合成数据10k/50k/200k行、段大小512、每模式一次预热、三次交替B/C重复。54条试次及九个DuckDB 1.4.0正确性对照均通过，三个有序选择性规模均达到至少80%求值行减少目标。[新原始结果](results/layout-repair-20261013.json)保留准备、保存/加载开销、逐次结果与源码哈希。

<!-- REPAIR_RESULTS_START -->
| Rows / 行数 | Workload / 负载 | B ms | C ms | Fewer evaluated rows / 求值行减少 |
|---:|---|---:|---:|---:|
| 10000 | ordered_selective | 0.240 | 0.047 | 94.88% |
| 10000 | shuffled_selective | 0.314 | 0.326 | 0.00% |
| 10000 | ordered_all | 0.898 | 0.931 | 0.00% |
| 50000 | ordered_selective | 1.141 | 0.155 | 97.95% |
| 50000 | shuffled_selective | 1.578 | 1.736 | 0.00% |
| 50000 | ordered_all | 4.813 | 5.035 | 0.00% |
| 200000 | ordered_selective | 4.613 | 0.566 | 98.72% |
| 200000 | shuffled_selective | 6.488 | 6.488 | 0.00% |
| 200000 | ordered_all | 19.187 | 19.409 | 0.00% |
<!-- REPAIR_RESULTS_END -->

六个打乱或全扫描案例仍没有剪枝。10k/50k/200k打乱负载的C中位耗时分别比B高3.88%、10.00%、0.0045%；最后一项按毫秒舍入后相同，不能据此认定有实际意义的退化。全扫描C中位耗时分别高3.71%、4.59%、1.16%。这些是三次重复的描述性结果，不是统计不确定性估计。本项目仍是范围明确的工程复现，不能据此宣称超过DuckDB或研究成熟；两次不同日期运行的差异也不能单独归因于修复。

### 历史测量 — 初始实现

运行`segmentlens-bec82c0d6994`：Apple M1 Pro16GiB、Python3.12.2/NumPy2.3.3、CPU单BLAS线程、合成数据、段512，一次预热、三次交替配对重复。表内为仅查询耗时的毫秒中位数；导入/加载成本与逐次结果见[原始JSON](results/benchmark.json)。B/C输出及原生DuckDB1.4.0正确性参考一致；预设各有序规模至少80%行工作量减少目标全部达到。

<!-- RESULTS_START -->
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
<!-- RESULTS_END -->

无序数据无剪枝收益，本次各规模C均更慢。求值行不等于物理磁盘字节、RSS或上游吞吐。数组全量载入内存，只支持有限float64/Unicode，无NULL、SQL解析、join、更新或崩溃安全事务。详见[限制](docs/zh/LIMITATIONS.md)。这是实验软件，不是生产数据库。

## 文档与维护

[UPSTREAM_ANALYSIS](docs/zh/UPSTREAM_ANALYSIS.md) · [REPRODUCTION](docs/zh/REPRODUCTION.md) · [DESIGN](docs/zh/DESIGN.md) · [IMPROVEMENTS](docs/zh/IMPROVEMENTS.md) · [EXPERIMENTS](docs/zh/EXPERIMENTS.md) · [DEVELOPMENT_LOG](docs/zh/DEVELOPMENT_LOG.md) · [WALKTHROUGH](docs/zh/WALKTHROUGH.md) · [LIMITATIONS](docs/zh/LIMITATIONS.md)

统一入口：make test/demo/bench/report/build。`docker build -t segmentlens .`、`docker run --rm segmentlens`运行CPU示例。宿主机无Docker，容器状态请检查[真实CI](https://github.com/hardwork-xu/columnar-query-engine/actions/workflows/ci.yml)。

自主代码采用MIT。[第三方归属](THIRD_PARTY.md)、[NOTICE](NOTICE)、[贡献指南](CONTRIBUTING_zh.md)、[安全说明](SECURITY.md)、[版本说明](CHANGELOG.md)。引用元数据见[CITATION.cff](CITATION.cff)，上游架构及成熟机制应归属[DuckDB](https://github.com/duckdb/duckdb)。
