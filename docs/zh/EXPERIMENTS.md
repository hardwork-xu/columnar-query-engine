# 实验

run_id为`segmentlens-bec82c0d6994`，源码提交`67dc02f2f459f77e92a80911ebe5704098ce4e7a`，测量时工作树干净。[原始JSON](../../results/benchmark.json)记录54条配对试次、配置、数据与源码哈希、UTC时间、建表/保存/加载开销和状态。环境：Apple M1 Pro、16 GiB、macOS 26.6.2 arm64、Python 3.12.2、NumPy 2.3.3，仅CPU，BLAS线程变量均为1。原生正确性参考DuckDB 1.4.0为单线程；不是研究SHA，也不是上游速度实验。

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
