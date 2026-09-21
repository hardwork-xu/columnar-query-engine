import json
import subprocess
import sys
import pytest
from segmentlens import Table
from segmentlens.benchmark import report, run_benchmark


def test_cli_demo_and_failure():
    p = subprocess.run([sys.executable, '-m', 'segmentlens', 'demo'], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    r = json.loads(p.stdout)
    assert r['B']['rows'] == r['C']['rows']
    assert r['C']['stats']['rows_evaluated'] < r['B']['stats']['rows_evaluated']
    p = subprocess.run([sys.executable, '-m', 'segmentlens', 'query', 'missing.npz', 'missing.json'], capture_output=True, text=True)
    assert p.returncode == 2 and '错误' in p.stderr


def test_cli_persistence_integration(tmp_path):
    p = tmp_path / 'data.npz'
    Table({'x': [1, 2, 3], 'g': ['a', 'a', 'b']}).save(p)
    spec = tmp_path / 'query.json'
    spec.write_text(json.dumps({'measure': 'x', 'group_by': 'g'}))
    r = subprocess.run([sys.executable, '-m', 'segmentlens', 'query', str(p), str(spec), '--no-prune'], capture_output=True, text=True)
    assert r.returncode == 0
    assert json.loads(r.stdout)['rows'][0]['sum'] == 3


def test_experiment_schema(tmp_path):
    # 10k is the smallest preregistered scale; avoid changing targets for a tiny test.
    p = tmp_path / 'run.json'
    r = run_benchmark(p, sizes=(10000,), repeats=1)
    assert r['status'] == 'passed' and not r['failures']
    assert len(r['cases']) == 3
    assert all(t['correct'] for c in r['cases'] for t in c['trials'])
    assert r['cases'][0]['target_met']
    assert 'ordered_selective' in report(p)
    assert json.loads(p.read_text())['run_id'] == r['run_id']
    with pytest.raises(FileExistsError):
        run_benchmark(p)


def test_recorded_results_schema_if_present():
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / 'results' / 'benchmark.json'
    if path.exists():
        r = json.loads(path.read_text())
        assert r['schema_version'] == 1 and r['status'] == 'passed'
        assert r['source']['commit'] and not r['source']['dirty']
        assert len(r['cases']) == 9
        assert all(t['correct'] for c in r['cases'] for t in c['trials'])


def test_failed_report_and_invalid_archive_cli(tmp_path):
    import numpy as np
    path = tmp_path / 'failed.json'
    path.write_text(json.dumps({'schema_version': 1, 'status': 'failed', 'cases': []}))
    with pytest.raises(ValueError):
        report(path)
    archive = tmp_path / 'invalid.npz'
    np.savez(archive, __header__='[]', x=[1.0])
    query = tmp_path / 'query.json'
    query.write_text('{"measure":"x", "group_by":"x"}')
    p = subprocess.run([sys.executable, '-m', 'segmentlens', 'query', str(archive), str(query)], text=True, capture_output=True)
    assert p.returncode == 2
    assert 'Traceback' not in p.stderr and '归档' in p.stderr
