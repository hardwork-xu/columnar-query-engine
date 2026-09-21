# 代码导读

阅读顺序：tests/test_engine.py契约 → engine.Table自有数据及摘要 → _validated → _possible保守单边判断 → _mask与execute选择归约 → benchmark.run_benchmark → 原始试次。

入口链：__main__ → cli.main → Table/Query → execute。不变量：摘要返回false必须意味着没有任何匹配行；无法判定必须返回true。B/C只在整段排除上不同，不能改变查询或近似输出。调试时在_possible打断点，用test_pruning_and_unfavorable_cases观察10段中跳过9段，标量参考保持一致。

增加运算符须同步修改类型验证、行mask和保守摘要，并测试极值相等边界；不能安全判定时返回true。增加NULL前应明确三值逻辑和count/sum语义，直接以NaN代替并不正确。公共接口参数和输出见对应DESIGN页面。
