import argparse
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def run_solver(solver: str, cnf: str, n_threads: int) -> float:
    """Run solver on a single CNF file and return elapsed time."""
    print(f"  [*] Запуск решения {cnf}")
    start = time.perf_counter()
    subprocess.run([solver, cnf, f"--nThreads={n_threads}"], stdout=subprocess.DEVNULL)
    end = time.perf_counter()
    elapsed = end - start
    print(f"      [+] Время: {elapsed:.3f} сек")
    return elapsed


def collect_gprof(solver: str, gmon_file: str = "gmon.out") -> Dict[str, float]:
    """Return mapping from function name to self seconds using gprof | head."""
    try:
        result = subprocess.run(
            ["bash", "-c", f"gprof {solver} {gmon_file} | head"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("[!] gprof not found")
        return {}

    if result.returncode != 0:
        return {}

    lines = result.stdout.splitlines()
    profile: Dict[str, float] = {}
    capture = False
    for line in lines:
        if line.strip().endswith("name"):
            capture = True
            continue
        if not capture:
            continue
        if not line.strip():
            if profile:
                break
            else:
                continue
        parts = line.split()
        if len(parts) < 7:
            continue
        try:
            self_sec = float(parts[2])
        except ValueError:
            continue
        func = parts[-1]
        profile[func] = self_sec
        if len(profile) >= 5:
            break
    return profile


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
    cnf_files = os.listdir(args.cnf_folder)
    print(f"[*] Найдено файлов: {len(cnf_files)}")

    profiles: List[Dict[str, float]] = []

    for cnf_file in cnf_files:
        elapsed = run_solver(
            args.solver, os.path.join(args.cnf_folder, cnf_file), args.threads
        )
        total_time += elapsed
        count += 1
        print(f"      [=] Суммарно: {elapsed:.3f} сек")
        prof = collect_gprof(args.solver)
        if prof:
            profiles.append(prof)

    if count == 0:
        print(f"[!] No .cnf files found in {args.cnf_folder}")
        return

    average_time = total_time / count
    print(f"[*] Среднее время: {average_time:.3f} сек")
    report = [f"Average solving time for {count} CNFs: {average_time:.3f} seconds"]

    if profiles:
        agg: Dict[str, float] = {}
        cnt: Dict[str, int] = {}
        for prof in profiles:
            for func, val in prof.items():
                agg[func] = agg.get(func, 0.0) + val
                cnt[func] = cnt.get(func, 0) + 1
        avg_prof = {func: agg[func] / cnt[func] for func in agg}
        top_funcs = sorted(avg_prof.items(), key=lambda x: x[1], reverse=True)[:5]
        report.append("")
        report.append("Top 5 functions:")
        for func, val in top_funcs:
            report.append(f"{val:.6f} {func}")

    timestamp = datetime.now().strftime("%Y.%m.%d_%H:%M:%S")
    report_file = bench_dir / f"benchmark_{timestamp}.txt"
    report_file.write_text("\n".join(report))
    print(f"[*] Отчёт сохранён в {report_file}")


if __name__ == "__main__":
    main()
