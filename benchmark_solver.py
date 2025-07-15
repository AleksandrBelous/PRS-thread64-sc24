import argparse
import glob
import os
import subprocess
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def parse_gprof_output(gprof_output):
    lines = gprof_output.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip().startswith('%') and 'time' in line and 'cumulative' in line:
            start = idx + 1
            break
    if start is None:
        return []
    entries = []
    for line in lines[start:]:
        if not line.strip():
            break
        parts = line.split()
        if len(parts) < 7:
            continue
        try:
            self_sec = float(parts[2])
        except ValueError:
            continue
        func_name = parts[-1]
        entries.append((func_name, self_sec))
        if len(entries) >= 5:
            break
    return entries


def run_solver(solver, cnf, prefix, n_threads):
    env = os.environ.copy()
    env['GMON_OUT_PREFIX'] = str(prefix)
    start = time.perf_counter()
    subprocess.run([solver, cnf, f'--nThreads={n_threads}'], env=env, stdout=subprocess.DEVNULL)
    end = time.perf_counter()
    return end - start


def main():
    parser = argparse.ArgumentParser(description='Benchmark PRS solver.')
    parser.add_argument('solver', help='Path to solver binary')
    parser.add_argument('cnf_folder', help='Directory with CNF files')
    parser.add_argument('--threads', type=int, default=2, help='Number of threads for solver')
    args = parser.parse_args()

    bench_dir = Path('benchmarks')
    bench_dir.mkdir(exist_ok=True)
    prefix = bench_dir / 'gmon'

    for f in glob.glob(f"{prefix}.*"):
        os.remove(f)

    total_time = 0.0
    count = 0
    func_sum = defaultdict(float)
    func_count = defaultdict(int)

    cnf_files = sorted(Path(args.cnf_folder).glob('*.cnf'))
    for cnf_file in cnf_files:
        elapsed = run_solver(args.solver, str(cnf_file), prefix, args.threads)
        total_time += elapsed
        count += 1

        for gmon_file in glob.glob(f"{prefix}.*"):
            result = subprocess.run(
                ['gprof', args.solver, gmon_file],
                capture_output=True,
                text=True,
            )
            entries = parse_gprof_output(result.stdout)
            for func, self_time in entries:
                func_sum[func] += self_time
                func_count[func] += 1
            os.remove(gmon_file)

    if count == 0:
        print(f"[!] No .cnf files found in {args.cnf_folder}")
        return

    average_time = total_time / count
    report = [f"Average solving time for {count} CNFs: {average_time:.3f} seconds", '', 'Top 5 functions:']

    averages = [
        (func_sum[f] / func_count[f], f)
        for f in func_sum
    ]
    for avg, name in sorted(averages, reverse=True)[:5]:
        report.append(f"{avg:.6f} {name}")

    timestamp = datetime.now().strftime('%Y.%m.%d_%H:%M:%S')
    report_file = bench_dir / f"benchmark_{timestamp}.txt"
    report_file.write_text('\n'.join(report))
    print(f"[*] Profile saved to {report_file}")


if __name__ == '__main__':
    main()
