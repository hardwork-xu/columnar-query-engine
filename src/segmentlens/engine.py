"""Typed vector selection and aggregation. 类型化向量选择与聚合。"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from types import MappingProxyType
import numpy as np


@dataclass(frozen=True)
class Predicate:
    """One typed condition; conditions are ANDed. 单个类型化条件，条件之间取交集。"""
    column: str
    op: str
    value: object


@dataclass(frozen=True)
class Query:
    """Grouped count and sum over selected rows. 对筛选行分组计数并求和。"""
    measure: str
    group_by: str
    predicates: tuple[Predicate, ...] = ()

    @classmethod
    def from_dict(cls, value: dict) -> Query:
        """Parse a strict JSON query object. 解析严格的JSON查询对象。"""
        if not isinstance(value, dict) or set(value) - {'measure', 'group_by', 'predicates'}:
            raise ValueError('invalid query fields / 查询字段无效')
        try:
            return cls(value['measure'], value['group_by'], tuple(Predicate(**p) for p in value.get('predicates', [])))
        except (KeyError, TypeError) as exc:
            raise ValueError('invalid query structure / 查询结构无效') from exc


@dataclass
class Result:
    """Rows plus explicit execution counters. 结果行与明确执行计数。"""
    rows: list[dict]
    stats: dict

    def to_dict(self) -> dict:
        return {'rows': self.rows, 'stats': self.stats}


class Table:
    """Owned read-only columns; load/save never uses pickle. 自有只读列，保存加载不使用pickle。"""
    def __init__(self, columns: dict, segment_size: int = 512):
        if not isinstance(segment_size, int) or isinstance(segment_size, bool) or segment_size < 1:
            raise ValueError('segment_size must be positive / 段大小必须为正整数')
        if not isinstance(columns, dict) or not columns:
            raise ValueError('at least one column required / 至少需要一列')
        owned = {}
        length = None
        for name, values in columns.items():
            if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', name):
                raise ValueError('invalid column name / 列名无效')
            a = np.asarray(values)
            if a.ndim != 1 or a.dtype.kind not in 'fiuU':
                raise ValueError('columns must be 1D numbers or Unicode / 列必须是一维数值或Unicode')
            if a.dtype.kind in 'iu' and a.size and (np.any(a > 2**53) or np.any(a < -(2**53))):
                raise ValueError('integer exceeds float64 exact range / 整数超出float64精确范围')
            a = np.array(a, dtype=np.float64 if a.dtype.kind != 'U' else a.dtype, copy=True)
            if a.dtype.kind == 'f' and not np.isfinite(a).all():
                raise ValueError('non-finite values unsupported / 不支持非有限数值')
            if length is not None and len(a) != length:
                raise ValueError('column lengths differ / 列长度不一致')
            length = len(a)
            a.flags.writeable = False
            owned[name] = a
        self._columns = owned
        self.segment_size = segment_size
        self.length = length

    @property
    def columns(self):
        """Expose read-only views; do not mutate bases. 返回只读视图，请勿修改底层数组。"""
        views = {k: v.view() for k, v in self._columns.items()}
        return MappingProxyType(views)

    def save(self, path: str | Path):
        """Write a new NPZ file; refuse replacement. 写入新NPZ文件，拒绝覆盖。"""
        path = Path(path)
        if path.suffix != '.npz':
            raise ValueError('use .npz extension / 使用.npz扩展名')
        header = json.dumps({'format': 1, 'segment_size': self.segment_size})
        with path.open('xb') as stream:
            np.savez(stream, __header__=np.array(header), **self._columns)

    @classmethod
    def load(cls, path: str | Path) -> Table:
        """Load and validate complete data, then reconstruct metadata. 全量加载验证后重建元数据。"""
        with np.load(path, allow_pickle=False) as archive:
            header = json.loads(str(archive['__header__']))
            if header.get('format') != 1:
                raise ValueError('unsupported format / 不支持的格式')
            return cls({k: archive[k] for k in archive.files if k != '__header__'}, header['segment_size'])


def _validated(table: Table, query: Query) -> tuple[Predicate, ...]:
    if not isinstance(query, Query):
        raise ValueError('Query required / 需要Query对象')
    if query.measure not in table._columns or query.group_by not in table._columns:
        raise ValueError('unknown measure/group column / 度量或分组列不存在')
    if table._columns[query.measure].dtype.kind != 'f':
        raise ValueError('measure must be numeric / 度量必须为数值')
    result = []
    for p in query.predicates:
        if not isinstance(p, Predicate) or p.column not in table._columns:
            raise ValueError('unknown predicate column / 谓词列不存在')
        numeric = table._columns[p.column].dtype.kind == 'f'
        if p.op not in ({'eq', 'lt', 'le', 'gt', 'ge', 'between', 'in'} if numeric else {'eq', 'in'}):
            raise ValueError('unsupported typed operator / 不支持该类型运算符')
        values = p.value if p.op in {'between', 'in'} else [p.value]
        if not isinstance(values, (list, tuple)) or (p.op == 'between' and len(values) != 2):
            raise ValueError('invalid predicate values / 谓词值无效')
        normalized = []
        for value in values:
            if numeric:
                if isinstance(value, (bool, str)) or not isinstance(value, (int, float)) or not np.isfinite(value):
                    raise ValueError('finite numeric predicate required / 需要有限数值谓词')
                if isinstance(value, int) and abs(value) > 2**53:
                    raise ValueError('predicate integer loses precision / 谓词整数损失精度')
                normalized.append(float(value))
            elif not isinstance(value, str):
                raise ValueError('string predicate required / 需要字符串谓词')
            else:
                normalized.append(value)
        if p.op == 'between' and normalized[0] > normalized[1]:
            raise ValueError('reversed bounds / 区间上下界颠倒')
        result.append(Predicate(p.column, p.op, tuple(normalized) if p.op in {'between', 'in'} else normalized[0]))
    return tuple(result)


def _mask(a: np.ndarray, p: Predicate) -> np.ndarray:
    if p.op == 'eq':
        return a == p.value
    if p.op == 'lt':
        return a < p.value
    if p.op == 'le':
        return a <= p.value
    if p.op == 'gt':
        return a > p.value
    if p.op == 'ge':
        return a >= p.value
    if p.op == 'between':
        return (a >= p.value[0]) & (a <= p.value[1])
    return np.isin(a, p.value)


def execute(table: Table, query: Query, *, prune: bool = False) -> Result:
    """Run selection vectors then grouped aggregation. 先计算选择向量，再执行分组聚合。"""
    if prune:
        raise ValueError('pruning not implemented in baseline / 基线不支持剪枝')
    predicates = _validated(table, query)
    stats = {'segments_total': 0, 'segments_pruned': 0, 'rows_evaluated': 0, 'rows_matched': 0}
    groups = {}
    for start in range(0, table.length, table.segment_size):
        end = min(start + table.segment_size, table.length)
        stats['segments_total'] += 1
        stats['rows_evaluated'] += end - start
        selected = np.ones(end - start, dtype=bool)
        for p in predicates:
            selected &= _mask(table._columns[p.column][start:end], p)
        selection = np.flatnonzero(selected)
        stats['rows_matched'] += len(selection)
        keys = table._columns[query.group_by][start:end][selection]
        values = table._columns[query.measure][start:end][selection]
        unique, inverse = np.unique(keys, return_inverse=True)
        counts = np.bincount(inverse, minlength=len(unique))
        sums = np.bincount(inverse, weights=values, minlength=len(unique))
        for key, count, total in zip(unique, counts, sums):
            key = key.item()
            previous = groups.setdefault(key, [0, 0.0])
            previous[0] += int(count)
            previous[1] += float(total)
    rows = [{'key': key, 'count': groups[key][0], 'sum': groups[key][1]} for key in sorted(groups)]
    return Result(rows, stats)
