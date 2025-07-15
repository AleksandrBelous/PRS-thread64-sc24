import argparse
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path


def run_solver(solver: str, cnf: str, n_threads: int) -> float:
    """Run solver on a single CNF file and return elapsed time."""
    print(f"  [*] Запуск решения {cnf}")
    start = time.perf_counter()
    subprocess.run([solver, cnf, f"--nThreads={n_threads}"], stdout=subprocess.DEVNULL)
    end = time.perf_counter()
    elapsed = end - start
    print(f"      [+] Время: {elapsed:.3f} сек")
    return elapsed


def main():
    parser = argparse.ArgumentParser(description="Benchmark PRS solver.")
    parser.add_argument("solver", help="Path to solver binary")
    parser.add_argument("cnf_folder", help="Directory with CNF files")
    parser.add_argument(
        "--threads", type=int, default=2, help="Number of threads for solver"
    )
    args = parser.parse_args()

    bench_dir = Path("benchmarks")
    bench_dir.mkdir(exist_ok=True)

    total_time = 0.0
    count = 0

    print(f"[*] Поиск CNF-файлов в {args.cnf_folder}")
    cnf_files = [Path(args.cnf_folder).glob("*.cnf")]
    print(f"[*] Найдено файлов: {len(cnf_files)}")

    for cnf_file in cnf_files:
        elapsed = run_solver(args.solver, str(cnf_file), args.threads)
        total_time += elapsed
        count += 1
        print(f"      [=] Суммарно: {elapsed:.3f} сек")

    if count == 0:
        print(f"[!] No .cnf files found in {args.cnf_folder}")
        return

    average_time = total_time / count
    print(f"[*] Среднее время: {average_time:.3f} сек")
    report = [f"Average solving time for {count} CNFs: {average_time:.3f} seconds"]

    timestamp = datetime.now().strftime("%Y.%m.%d_%H:%M:%S")
    report_file = bench_dir / f"benchmark_{timestamp}.txt"
    report_file.write_text("\n".join(report))
    print(f"[*] Отчёт сохранён в {report_file}")


if __name__ == "__main__":
    main()
