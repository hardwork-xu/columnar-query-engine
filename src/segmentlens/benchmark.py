"""Reproducible B/C experiment; timing is secondary. 可复现实验，计时为次要指标。"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import time
import uuid
import numpy as np
from .engine import Predicate, Query, Table, execute


def source_info():
    root = Path(__file__).resolve().parents[2]
    def git(*args):
        p = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True)
        return p.stdout.strip() if p.returncode == 0 else None
    digest = hashlib.sha256()
    for p in sorted(Path(__file__).parent.glob('*.py')):
        digest.update(p.name.encode())
        digest.update(p.read_bytes())
    return {'commit': git('rev-parse', 'HEAD'), 'dirty': bool(git('status', '--porcelain')),
            'package_sha256': digest.hexdigest()}


def equal_rows(a, b):
    return (len(a) == len(b) and all(x['key'] == y['key'] and x['count'] == y['count'] and
            np.isclose(x['sum'], y['sum'], rtol=1e-10, atol=1e-10) for x, y in zip(a, b)))


def run_benchmark(output: str | Path, sizes=(10000, 50000, 200000), repeats=3, oracle=False):
    """Write all trials, status and environment as JSON. 以JSON保存全部试次、状态和环境。"""
    if repeats < 1 or not sizes or any(not isinstance(n, int) or n < 100 for n in sizes):
        raise ValueError('invalid experiment sizes/repeats / 实验规模或重复次数无效')
    output = Path(output)
    if output.exists():
        raise FileExistsError('refuse to overwrite experiment / 拒绝覆盖已有实验')
    raw = {'schema_version': 1, 'run_id': 'segmentlens-' + uuid.uuid4().hex[:12],
           'started_at': datetime.now(timezone.utc).isoformat(),
           'command': 'python -m segmentlens bench --output ' + output.as_posix() + (' --oracle-duckdb' if oracle else ''),
           'source': source_info(),
           'environment': {'os': platform.system(), 'os_release': platform.release(), 'machine': platform.machine(),
                           'python': platform.python_version(), 'numpy': np.__version__, 'cpu_count': os.cpu_count(),
                           'threads': {k: os.environ.get(k) for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']}},
           'config': {'sizes': list(sizes), 'repeats': repeats, 'warmups_per_mode': 1, 'segment_size': 512,
                      'seed': 20260921, 'sum_rtol': 1e-10, 'sum_atol': 1e-10, 'target_row_reduction': 0.8,
                      'data': 'synthetic', 'timing': 'query only; includes validation, filtering, aggregation',
                      'primary_metric': 'rows_evaluated; not disk bytes or RSS'},
           'upstream_A': {'status': 'not_run'}, 'cases': [], 'status': 'running', 'failures': []}
    connection = None
    try:
        if oracle:
            import duckdb
            connection = duckdb.connect()
            connection.execute('SET threads=1')
            raw['upstream_A'] = {'status': 'running', 'package': 'duckdb', 'version': importlib.metadata.version('duckdb'), 'scope': 'correctness only, separate release from source-study SHA'}
        for n in sizes:
            for workload in ['ordered_selective', 'shuffled_selective', 'ordered_all']:
                rng = np.random.default_rng(20260921 + n)
                x = np.arange(n, dtype=np.float64)
                if workload == 'shuffled_selective':
                    rng.shuffle(x)
                y = rng.normal(size=n)
                g = np.array(['alpha', 'beta', 'gamma', 'delta'])[rng.integers(0, 4, n)]
                lo, hi = (0., float(n)) if workload == 'ordered_all' else (n * .45, n * .46)
                query = Query('value', 'group', (Predicate('key', 'ge', lo), Predicate('key', 'lt', hi)))
                start = time.perf_counter()
                table = Table({'key': x, 'value': y, 'group': g}, 512)
                build_seconds = time.perf_counter() - start
                with tempfile.TemporaryDirectory() as td:
                    archive = Path(td) / 'table.npz'
                    start = time.perf_counter()
                    table.save(archive)
                    save_seconds = time.perf_counter() - start
                    archive_bytes = archive.stat().st_size
                    start = time.perf_counter()
                    loaded = Table.load(archive)
                    load_seconds = time.perf_counter() - start
                reference = execute(table, query, prune=False).rows
                if not equal_rows(execute(loaded, query).rows, reference):
                    raise AssertionError('persistence reference differs')
                oracle_equal = None
                if connection is not None:
                    connection.register('input_data', {'key': x, 'value': y, 'grp': g})
                    native = connection.execute('SELECT grp, count(*), sum(value) FROM input_data WHERE key >= ? AND key < ? GROUP BY grp ORDER BY grp', [lo, hi]).fetchall()
                    expected = [{'key': a, 'count': b, 'sum': c} for a, b, c in native]
                    oracle_equal = equal_rows(reference, expected)
                    if not oracle_equal:
                        raise AssertionError('DuckDB reference differs')
                case = {'n': n, 'workload': workload, 'query': {'lo': lo, 'hi_exclusive': hi},
                        'data_sha256': hashlib.sha256(x.tobytes() + y.tobytes() + g.tobytes()).hexdigest(),
                        'ingestion': {'build_seconds': build_seconds, 'save_seconds': save_seconds,
                                      'load_seconds': load_seconds, 'archive_bytes': archive_bytes},
                        'reference_rows': reference, 'upstream_A_equal': oracle_equal, 'trials': []}
                raw['cases'].append(case)
                for mode in (False, True):
                    execute(table, query, prune=mode)
                for repeat in range(repeats):
                    order = [False, True] if repeat % 2 == 0 else [True, False]
                    for prune in order:
                        start = time.perf_counter()
                        result = execute(table, query, prune=prune)
                        seconds = time.perf_counter() - start
                        correct = equal_rows(reference, result.rows)
                        case['trials'].append({'repeat': repeat, 'mode': 'C' if prune else 'B', 'seconds': seconds,
                                               'stats': result.stats, 'correct': correct, 'status': 'passed' if correct else 'failed'})
                        if not correct:
                            raise AssertionError('B/C result differs')
                b = next(t for t in case['trials'] if t['mode'] == 'B')['stats']['rows_evaluated']
                c = next(t for t in case['trials'] if t['mode'] == 'C')['stats']['rows_evaluated']
                case['row_reduction'] = 1 - c / b
                case['target_applicable'] = workload == 'ordered_selective'
                case['target_met'] = case['row_reduction'] >= .8 if case['target_applicable'] else None
                if case['target_met'] is False:
                    raise AssertionError('preregistered row-reduction target not met')
        raw['status'] = 'passed'
        if connection is not None:
            raw['upstream_A']['status'] = 'passed'
    except Exception as exc:
        raw['status'] = 'failed'
        raw['failures'].append({'type': type(exc).__name__, 'message': str(exc)})
        raise
    finally:
        if connection is not None:
            connection.close()
        raw['finished_at'] = datetime.now(timezone.utc).isoformat()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(raw, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    return raw


def report(path: str | Path) -> str:
    """Render the same table for both READMEs. 为双语README生成同一张表。"""
    data = json.loads(Path(path).read_text())
    lines = ['| Rows / 行数 | Workload / 负载 | B ms | C ms | Fewer evaluated rows / 求值行减少 |', '|---:|---|---:|---:|---:|']
    for c in data['cases']:
        times = {mode: float(np.median([t['seconds'] for t in c['trials'] if t['mode'] == mode])) * 1000 for mode in ('B', 'C')}
        lines.append(f"| {c['n']} | {c['workload']} | {times['B']:.3f} | {times['C']:.3f} | {c['row_reduction']:.2%} |")
    return '\n'.join(lines)
