# 设计与公共接口

Table(columns, segment_size=512)复制并拥有一维数值/Unicode列。数值使用有限float64，拒绝超出±2^53精确范围的整数。各列等长，只读视图防止普通误修改；允许空表。这不是防御恶意Python代码修改私有存储的安全边界。

Predicate(column, op, value)支持数值eq/lt/le/gt/ge/between/in，字符串eq/in；between包含两端。Query(measure, group_by, predicates=())按条件交集筛选并执行分组count/sum。Query.from_dict拒绝未知字段。execute(table, query, prune=False)运行B，prune=True运行C（默认）。Result.rows是按key排序的key/count/sum列表；Result.stats记录段数、跳过段数、求值行和匹配行。无结果返回[]，sum溢出报错。

C在分配布尔mask之前检查段摘要。数值范围可能重叠但无行命中，这只增加扫描，不会丢结果。字符串最多保存256个不同值，超限则完整扫描。选择向量按行索引收集度量与分组列；NumPy unique/bincount执行段内归约，Python字典合并段间结果。

N行、C列、批大小b、全局分组G：数据O(NC)，数值摘要O(NC/b)，类别摘要最坏O(256NC/b)，临时mask/索引O(b)，输出O(G)。局部unique约O(b log b)。最坏情况下C执行完整扫描并付出摘要检查开销，无并行worker状态。

Table.save拒绝覆盖已有.npz；Table.load禁用pickle，全量验证并重建摘要。这是可信本地文件接口，不是事务系统或恶意压缩包沙箱；加载包含全部列。查询计时排除构建和NPZ加载，两者另行记录。文件/归档使用上下文管理，实验临时目录结束自动清理。
