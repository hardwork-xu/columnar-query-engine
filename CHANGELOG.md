# Changelog / 版本说明

## Unreleased — 2026-10-13

Prevent public table-layout reassignment from invalidating pruning summaries. Protect experiment outputs with exclusive creation and retain failed-run records. Historical performance remains attributed to its measured source; the repaired implementation has not been benchmarked.

拒绝公开表布局重新赋值，避免摘要失效；排他创建实验文件并保留失败记录。历史性能仍归属于原测量源码，修复版尚未进行性能测量。

## 0.1.0 — 2026-09-21

Experimental release: independently implemented typed column batches, selection-vector filtering, grouped count/sum, conservative segment summaries, non-pickle persistence, bilingual CLI, tests, and measured B/C experiments. No SQL database or upstream superiority claim.

实验版本：独立类型化列批次、选择向量过滤、分组count/sum、保守段摘要、禁用pickle的保存加载、双语CLI、测试及实测B/C实验。不声称完整SQL数据库或优于上游。
