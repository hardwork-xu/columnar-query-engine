"""Bilingual CLI / 双语命令行。"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from .engine import Predicate, Query, Table, execute


def main(argv=None):
    parser = argparse.ArgumentParser(description='SegmentLens: columnar filters / 列式过滤与聚合')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo', help='run a real selection pipeline / 运行真实选择流水线')
    query = commands.add_parser('query', help='query an NPZ table / 查询NPZ表')
    query.add_argument('table', help='NPZ path / NPZ路径')
    query.add_argument('spec', help='JSON query file / JSON查询文件')
    query.add_argument('--no-prune', action='store_true', help='use baseline B / 使用基线B')
    bench = commands.add_parser('bench', help='run B/C experiment / 运行B/C实验')
    bench.add_argument('--output', default='results/local-benchmark.json', help='new JSON result / 新JSON结果文件')
    bench.add_argument('--oracle-duckdb', action='store_true', help='optional DuckDB reference / 可选DuckDB参考')
    analyze = commands.add_parser('report', help='render result table / 生成结果表')
    analyze.add_argument('result', help='result JSON path / 结果JSON路径')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            table = Table({'time': np.arange(4096), 'amount': np.ones(4096), 'category': ['sensor'] * 4096}, 128)
            q = Query('amount', 'category', (Predicate('time', 'between', [2000, 2099]),))
            print(json.dumps({'B': execute(table, q, prune=False).to_dict(), 'C': execute(table, q).to_dict()}, ensure_ascii=False, indent=2))
        elif args.command == 'query':
            q = Query.from_dict(json.loads(Path(args.spec).read_text()))
            print(json.dumps(execute(Table.load(args.table), q, prune=not args.no_prune).to_dict(), ensure_ascii=False, indent=2))
        elif args.command == 'bench':
            from .benchmark import run_benchmark
            r = run_benchmark(args.output, oracle=args.oracle_duckdb)
            print(json.dumps({'run_id': r['run_id'], 'status': r['status'], 'result': args.output}))
        else:
            from .benchmark import report
            print(report(args.result))
        return 0
    except (ValueError, KeyError, TypeError, OSError, ImportError, AssertionError) as exc:
        print(f'Error / 错误: {exc}', file=sys.stderr)
        return 2
