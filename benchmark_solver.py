import argparse
from ast import arg
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class GprofEntry:
    """Single line of gprof flat profile."""

    pct_time: float
    cumulative: float
    self_sec: float
    calls: Optional[float]
    self_per_call: Optional[float]
    total_per_call: Optional[float]
    name: str


def run_solver(solver: str, cnf: str, n_threads: int) -> float:
    """Run solver on a single CNF file and return elapsed time."""
    print(f"    [*] Запуск решения {cnf}")
    start = time.perf_counter()
    subprocess.run([solver, cnf, f"--nThreads={n_threads}"], stdout=subprocess.DEVNULL)
    end = time.perf_counter()
    elapsed = end - start
    print(f"        [+] Время: {elapsed:.3f} сек")
    return elapsed


def collect_gprof(
    solver: str, gmon_file: str = "gmon.out", limit: int = 5
) -> Tuple[float, List[GprofEntry]]:
    """Возвращает top функций из вывода `gprof | head`."""
    try:
        result = subprocess.run(
            ["bash", "-c", f"gprof {solver} {gmon_file} | head"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("[!] gprof not found")
        return 0.0, []

    if result.returncode != 0:
        return 0.0, []

    lines = result.stdout.splitlines()
    sample_unit = 0.0
    entries: List[GprofEntry] = []
    capture = False
    for line in lines:
        if "Each sample counts" in line:
            m = re.search(r"Each sample counts as\s+([0-9.]+)\s+seconds", line)
            if m:
                sample_unit = float(m.group(1))
            continue
        if line.strip().startswith("time") and "name" in line:
            capture = True
            continue
        if not capture:
            continue
        if not line.strip():
            if entries:
                break
            else:
                continue
        parts = line.split()
        if len(parts) < 4:
            continue
        name = parts[-1]
        nums = parts[:-1]
        try:
            pct = float(nums[0])
            cumulative = float(nums[1])
            self_sec = float(nums[2])
        except ValueError:
            continue
        calls = self_per_call = total_per_call = None
        if len(nums) >= 4:
            try:
                calls = float(nums[3])
            except ValueError:
                calls = None
        if len(nums) >= 5:
            try:
                self_per_call = float(nums[4])
            except ValueError:
                self_per_call = None
        if len(nums) >= 6:
            try:
                total_per_call = float(nums[5])
            except ValueError:
                total_per_call = None
        entries.append(
            GprofEntry(
                pct_time=pct,
                cumulative=cumulative,
                self_sec=self_sec,
                calls=calls,
                self_per_call=self_per_call,
                total_per_call=total_per_call,
                name=name,
            )
        )
        if limit and len(entries) >= limit:
            break
    return sample_unit, entries


def main():
    parser = argparse.ArgumentParser(description="Benchmark PRS solver.")
    parser.add_argument("solver", help="Path to solver binary")
    parser.add_argument("cnf_folder", help="Directory with CNF files")
    parser.add_argument(
        "--threads", type=int, default=4, help="Number of threads for solver"
    )
    args = parser.parse_args()

    bench_dir = Path(f"benchmarks_{args.cnf_folder.split('_')[-1]}")
    bench_dir.mkdir(exist_ok=True)

    total_time = 0.0
    count = 0

    print(f"[*] Поиск CNF-файлов в {args.cnf_folder}")
    cnf_files = os.listdir(args.cnf_folder)
    print(f"[*] Найдено файлов: {len(cnf_files)}")

    profiles: List[List[GprofEntry]] = []
    sample_units: List[float] = []

    for cnf_file in cnf_files:
        elapsed = run_solver(
            args.solver, os.path.join(args.cnf_folder, cnf_file), args.threads
        )
        total_time += elapsed
        count += 1
        print(f"        [=] Суммарно: {elapsed:.3f} сек")
        unit, prof = collect_gprof(args.solver)
        if prof:
            sample_units.append(unit)
            profiles.append(prof)

    if count == 0:
        print(f"[!] No .cnf files found in {args.cnf_folder}")
        return

    average_time = total_time / count
    print(f"[*] Среднее время: {average_time:.3f} сек")
    report = [f"Average solving time for {count} CNFs: {average_time:.3f} seconds"]

    if profiles:
        agg: Dict[str, Dict[str, float]] = {}
        for prof in profiles:
            for entry in prof:
                info = agg.setdefault(
                    entry.name,
                    {
                        "pct_sum": 0.0,
                        "self_sum": 0.0,
                        "calls_sum": 0.0,
                        "total_sum": 0.0,
                        "count": 0,
                        "has_calls": False,
                        "has_total": False,
                    },
                )
                info["pct_sum"] += entry.pct_time
                info["self_sum"] += entry.self_sec
                info["count"] += 1
                if entry.calls is not None:
                    info["calls_sum"] += entry.calls
                    info["has_calls"] = True
                if entry.total_per_call is not None and entry.calls is not None:
                    info["total_sum"] += entry.total_per_call * entry.calls
                    info["has_total"] = True

        avg_entries: List[GprofEntry] = []
        for name, info in agg.items():
            cnt_runs = info["count"]
            avg_self = info["self_sum"] / cnt_runs
            avg_pct = info["pct_sum"] / cnt_runs
            avg_calls = info["calls_sum"] / cnt_runs if info["has_calls"] else None
            avg_total_sec = info["total_sum"] / cnt_runs if info["has_total"] else None
            if avg_calls and avg_calls != 0:
                avg_self_call = avg_self / avg_calls
                avg_total_call = (
                    avg_total_sec / avg_calls if avg_total_sec is not None else None
                )
            else:
                avg_self_call = None
                avg_total_call = None
            avg_entries.append(
                GprofEntry(
                    pct_time=avg_pct,
                    cumulative=0.0,  # will be filled later
                    self_sec=avg_self,
                    calls=avg_calls,
                    self_per_call=avg_self_call,
                    total_per_call=avg_total_call,
                    name=name,
                )
            )

        avg_entries.sort(key=lambda e: e.self_sec, reverse=True)

        sample_unit = sum(sample_units) / len(sample_units) if sample_units else 0.0
        report.append("")
        report.append(f"Each sample counts as {sample_unit:.2f} seconds.")
        report.append("  %   cumulative   self              self     total           ")
        report.append(" time   seconds   seconds    calls   s/call   s/call  name    ")

        cumulative = 0.0
        for entry in avg_entries[:5]:
            cumulative += entry.self_sec
            calls_str = f"{int(entry.calls):d}" if entry.calls is not None else ""
            self_call_str = (
                f"{entry.self_per_call:.2f}" if entry.self_per_call is not None else ""
            )
            total_call_str = (
                f"{entry.total_per_call:.2f}"
                if entry.total_per_call is not None
                else ""
            )
            line = (
                f"{entry.pct_time:6.2f} {cumulative:10.2f} "
                f"{entry.self_sec:9.2f} "
                f"{calls_str:>9} {self_call_str:>8} {total_call_str:>8}  {entry.name}"
            )
            report.append(line)

    timestamp = datetime.now().strftime("%Y.%m.%d_%H:%M:%S")
    report_file = (
        bench_dir / f"benchmark_{str(bench_dir).split('_')[-1]}_{timestamp}.txt"
    )
    report_file.write_text("\n".join(report))
    print(f"[*] Отчёт сохранён в {report_file}")


if __name__ == "__main__":
    main()
