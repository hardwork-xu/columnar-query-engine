import numpy as np
import pytest
from segmentlens import Predicate, Query, Table, execute


def test_baseline_and_roundtrip(tmp_path):
    t = Table({'x': [0, 1, 2, 3, 4], 'y': [2, 3, 5, 7, 11], 'g': ['a', 'b', 'a', 'b', 'a']}, 2)
    q = Query('y', 'g', (Predicate('x', 'ge', 1),))
    expected = [{'key': 'a', 'count': 2, 'sum': 16.0}, {'key': 'b', 'count': 2, 'sum': 10.0}]
    assert execute(t, q).rows == expected
    p = tmp_path / 'table.npz'
    t.save(p)
    assert execute(Table.load(p), q).rows == expected
    with pytest.raises(FileExistsError):
        t.save(p)
    with pytest.raises(ValueError):
        t.columns['x'][0] = 3


@pytest.mark.parametrize('columns', [{}, {'x': [[1]]}, {'x': [np.nan]}, {'x': [np.inf]}, {'x': [1], 'y': []}, {'x': [2**54]}, {'x': [None]}, {'bad/name': [1]}])
def test_invalid_table(columns):
    with pytest.raises(ValueError):
        Table(columns)


@pytest.mark.parametrize('predicate', [Predicate('z', 'eq', 1), Predicate('x', 'eq', np.nan), Predicate('x', 'between', [3, 1]), Predicate('x', 'wat', 1), Predicate('g', 'ge', 'a')])
def test_invalid_predicate(predicate):
    t = Table({'x': [1], 'g': ['a']})
    with pytest.raises(ValueError):
        execute(t, Query('x', 'g', (predicate,)))


def test_empty_and_owned_copy():
    assert execute(Table({'x': [], 'g': np.array([], dtype='U1')}), Query('x', 'g')).rows == []
    x = np.array([1.0, 2.0])
    t = Table({'x': x})
    x[0] = 100
    assert t.columns['x'][0] == 1


@pytest.mark.parametrize('op,value', [('eq', 15), ('lt', 15), ('le', 15), ('gt', 15), ('ge', 15), ('between', [7, 33]), ('in', [0, 15, 49]), ('in', [])])
def test_conservative_pruning_matches_scalar(op, value):
    rng = np.random.default_rng(93)
    x = rng.integers(0, 50, 601)
    y = rng.normal(size=601)
    g = np.array(['a', 'b', 'c'])[rng.integers(0, 3, 601)]
    t = Table({'x': x, 'y': y, 'g': g}, 11)
    q = Query('y', 'g', (Predicate('x', op, value),))
    ops = {'eq': lambda x: x == value, 'lt': lambda x: x < value, 'le': lambda x: x <= value,
           'gt': lambda x: x > value, 'ge': lambda x: x >= value,
           'between': lambda x: value[0] <= x <= value[1], 'in': lambda x: x in value}
    expected = {}
    for a, b, c in zip(x, y, g):
        if ops[op](a):
            pair = expected.setdefault(c, [0, 0.0])
            pair[0] += 1
            pair[1] += b
    for prune in [False, True]:
        rows = execute(t, q, prune=prune).rows
        assert [r['key'] for r in rows] == sorted(expected)
        for r in rows:
            assert r['count'] == expected[r['key']][0]
            assert r['sum'] == pytest.approx(expected[r['key']][1], rel=1e-10, abs=1e-10)


def test_pruning_and_unfavorable_cases():
    t = Table({'x': np.arange(100), 'g': ['a'] * 50 + ['b'] * 50}, 10)
    q = Query('x', 'g', (Predicate('x', 'between', [40, 49]), Predicate('g', 'in', ['a'])))
    b, c = execute(t, q, prune=False), execute(t, q, prune=True)
    assert b.rows == c.rows
    assert c.stats['rows_evaluated'] == 10
    assert c.stats['segments_pruned'] == 9
    broad = execute(t, Query('x', 'g', (Predicate('x', 'ge', 0),)))
    assert broad.stats['segments_pruned'] == 0
    assert broad.stats['rows_evaluated'] == 100


def test_categorical_high_cardinality_fallback():
    t = Table({'g': [f'key{i}' for i in range(300)], 'x': np.arange(300)}, 300)
    q = Query('x', 'g', (Predicate('g', 'eq', 'missing'),))
    assert execute(t, q).rows == []
    assert execute(t, q).stats['rows_evaluated'] == 300
    assert execute(t, Query('x', 'g', (Predicate('g', 'in', []),))).stats['rows_evaluated'] == 0


def test_strict_query_parser_and_numeric_groups():
    q = Query.from_dict({'measure': 'x', 'group_by': 'x', 'predicates': []})
    assert len(execute(Table({'x': [1, 1, 2]}), q).rows) == 2
    for invalid in [{}, {'measure': 'x', 'group_by': 'x', 'oops': True}, {'predicates': [5]}]:
        with pytest.raises(ValueError):
            Query.from_dict(invalid)
