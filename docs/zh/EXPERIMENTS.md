# 实验

**测量与源码边界（2026-10-13）。** 下方各表及原始文件分别对应自己的源码提交，初始历史证据完整保留。当前代码拒绝运行中重新赋值布局，并排他创建实验结果文件，预检查后出现其他文件或符号链接也不会被覆盖。普通实验异常在目标可用时仍保存 `failed` 记录；已占用路径始终保留。排他创建不保证写入进程崩溃时的原子性或耐久性。只读属性访问改变查询热路径；现已单独测量修复源码的 B/C 时延及准备成本，结果列在未改动的历史记录之前；结果格式功能测试不算性能证据。

## 修复后测量 — 2026-10-13

运行 `segmentlens-f0eea47a2116` 开始于 `2026-10-13T04:06:58.477380+00:00`，结束于 `2026-10-13T04:06:59.435200+00:00`，测量干净提交 `00c50b3c9413f2894909bcf2d8fa9ff2863492f6`，包SHA256为 `2e132bf70f993a54899c90af9444ac4c8a9edfb9334c46e8d1899b2c88dfd180`。[原始JSON](../../results/layout-repair-20261013.json)的SHA256为 `942c1e268718b1d5fa0d3287c1b101328133aef71ac7594cc9fa7dca00bb5b62`。

本次记录环境：Darwin 25.6.0 arm64、10个逻辑CPU、Python 3.12.2、NumPy 2.3.3；OMP/OPENBLAS/VECLIB线程变量均为1。协议配置与下方历史运行完全一致：三个规模、三种负载、每模式一次预热、三次交替B/C重复，共54条试次。仅查询中位数不包含另行记录的建表、保存和加载开销。九个案例均通过单线程DuckDB 1.4.0正确性对照；未测量DuckDB耗时。

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

三个有序选择性目标均通过：在10k/50k/200k行下，C求值512/1,024/2,560行，分别减少94.88%/97.952%/98.72%。计数完全一致，记录中sum满足原有rtol/atol 1e-10；54条B/C检查和九次原生对照全部通过，失败列表为空。独立的不计时复核根据保存的种子和配置重建输入哈希、分组参考及分段工作量计数；这属于原运行的核验，不是新增实验。

六个零剪枝负载完整保留。打乱负载C相对B耗时为+3.88%、+10.00%、+0.0045%；全扫描为+3.71%、+4.59%、+1.16%。200k打乱负载中位数只差约0.000292毫秒，表格舍入后相同；三次重复不足以建立其实际或统计意义。未建立置信区间或跨机器普适性。本次重测验证修复后的工程实现在该合成协议下的行为，不代表研究成熟、超过上游，或两次不同日期运行之间由修复引起的因果速度变化。

先从已提交结果生成表格；后续命令可选地在新路径重新运行，已有结果不会被覆盖：

```sh
python -m segmentlens report results/layout-repair-20261013.json
python -m pip install duckdb==1.4.0
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m segmentlens bench --output results/layout-repair-local.json --oracle-duckdb
python -m segmentlens report results/layout-repair-local.json
```

## 历史测量 — 初始实现

run_id为`segmentlens-bec82c0d6994`，源码提交`67dc02f2f459f77e92a80911ebe5704098ce4e7a`，测量时工作树干净。[原始JSON](../../results/benchmark.json)记录54条模式试次（27组B/C配对）、配置、数据与源码哈希、UTC时间、建表/保存/加载开销和状态。环境：Apple M1 Pro、16 GiB、macOS 26.6.2 arm64、Python 3.12.2、NumPy 2.3.3，仅CPU，BLAS线程变量均为1。原生正确性参考DuckDB 1.4.0为单线程；不是研究SHA，也不是上游速度实验。

固定种子20260921，规模10k/50k/200k，段512，4个分组，float64。窄区间[0.45N,0.46N)，分别测试有序和随机打乱键；全量区间[0,N)。每模式一次预热，三次重复并交替B/C顺序。计时包含查询输入校验、过滤和聚合；构建及加载另计。查询不依赖外部数据、模型、网络或设备传输。

主要目标为有序选择性负载各规模求值行至少减少80%，计数一致、sum的rtol/atol均1e-10。求值行是算法工作量，不是物理磁盘读取、内存或端到端吞吐。目标在实现前已提交，同时验证序列化往返和原生输出。全部断言通过，正式实验无失败试次；结果格式测试中的小实验不充当额外性能证据。

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

时间为毫秒中位数，逐次计时与零剪枝负面结果完整保留。不能将小型合成CPU结果外推为生产数据库性能。

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 python -m segmentlens bench --output results/local-benchmark.json
python -m segmentlens report results/local-benchmark.json
# 可选独立参考：
python -m pip install duckdb==1.4.0
# 使用新结果文件名，并在实验命令增加 --oracle-duckdb。
```

report从JSON生成两份README同一张表。结果文件拒绝覆盖。Docker在本地测量机器不可用；容器及CI状态应以实际远端workflow为准。
