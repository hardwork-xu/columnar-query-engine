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
