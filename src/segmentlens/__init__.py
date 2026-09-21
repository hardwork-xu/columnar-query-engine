"""SegmentLens public API / SegmentLens 公共接口。"""
from .engine import Predicate, Query, Result, Table, execute

__all__ = ['Predicate', 'Query', 'Result', 'Table', 'execute']
__version__ = '0.1.0'
