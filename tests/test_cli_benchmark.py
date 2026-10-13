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


@pytest.mark.parametrize('entry', ['file', 'symlink', 'dangling_symlink'])
def test_benchmark_rejects_occupied_output_before_work(tmp_path, monkeypatch, entry):
    import segmentlens.benchmark as benchmark

    output = tmp_path / 'run.json'
    target = tmp_path / 'target.json'
    if entry == 'file':
        output.write_text('prior evidence')
    else:
        if entry == 'symlink':
            target.write_text('prior evidence')
        output.symlink_to(target)
    def must_not_run():
        raise AssertionError('occupied output must fail before source discovery or measurement')
    monkeypatch.setattr(benchmark, 'source_info', must_not_run)
    with pytest.raises(FileExistsError):
        run_benchmark(output)
    if entry == 'file':
        assert output.read_text() == 'prior evidence'
    else:
        assert output.is_symlink()
        if entry == 'symlink':
            assert target.read_text() == 'prior evidence'
        else:
            assert not target.exists()


@pytest.mark.parametrize('entry', ['file', 'dangling_symlink'])
def test_benchmark_racing_destination_is_not_overwritten(tmp_path, monkeypatch, entry):
    import segmentlens.benchmark as benchmark

    output = tmp_path / 'run.json'
    target = tmp_path / 'target.json'
    original_source_info = benchmark.source_info
    def competing_writer():
        # This occurs after run_benchmark's preflight check.
        # 在 run_benchmark 的预检查之后模拟另一个写入者。
        if entry == 'file':
            output.write_text('concurrent evidence')
        else:
            output.symlink_to(target)
        return original_source_info()
    monkeypatch.setattr(benchmark, 'source_info', competing_writer)
    with pytest.raises(FileExistsError):
        run_benchmark(output, sizes=(10000,), repeats=1)
    if entry == 'file':
        assert output.read_text() == 'concurrent evidence'
    else:
        assert output.is_symlink() and not target.exists()


def test_benchmark_failure_keeps_failed_record(tmp_path, monkeypatch):
    import segmentlens.benchmark as benchmark

    output = tmp_path / 'failed.json'
    def fail_table(*args, **kwargs):
        raise ValueError('injected table validation failure')
    monkeypatch.setattr(benchmark, 'Table', fail_table)
    with pytest.raises(ValueError, match='injected table validation failure'):
        run_benchmark(output, sizes=(10000,), repeats=1)
    raw = json.loads(output.read_text())
    assert raw['status'] == 'failed' and raw['cases'] == []
    assert raw['failures'] == [{'type': 'ValueError', 'message': 'injected table validation failure'}]
    assert raw['finished_at'] and raw['source']['package_sha256']
    with pytest.raises(ValueError, match='complete successful'):
        report(output)
