#!/usr/bin/env python3
import os
import re
import sys
import argparse
from collections import defaultdict


def parse_file(path):
    avg_solve_time = None
    func_percents = {}
    # Первый проход — ищем строку со средней продолжительностью решения
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.search(r"Average solving time.*?:\s*([\d\.]+)\s*seconds", line)
            if m:
                avg_solve_time = float(m.group(1))
                break
    if avg_solve_time is None:
        raise ValueError(f"Average solving time not found in {path}")
    # Второй проход — парсим таблицу профилирования
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            # Строки данных начинаются с цифры после пробелов
            if re.match(r"^\s*\d", line):
                tokens = line.split()
                if len(tokens) < 2:
                    continue
                try:
                    percent = float(tokens[0])
                except ValueError:
                    continue
                name = tokens[-1]
                func_percents[name] = percent
    return avg_solve_time, func_percents


def main():
    parser = argparse.ArgumentParser(description="Aggregate profiling data")
    parser.add_argument("directory", help="Path to folder with profiling files")
    args = parser.parse_args()

    solve_times = []
    func_times = defaultdict(list)

    for fname in os.listdir(args.directory):
        path = os.path.join(args.directory, fname)
        if os.path.isfile(path):
            try:
                avg_solve, percents = parse_file(path)
            except Exception as e:
                print(f"Warning: {e}", file=sys.stderr)
                continue
            solve_times.append(avg_solve)
            for name, percent in percents.items():
                func_times[name].append(percent)

    if not solve_times or not func_times:
        print("No valid profiling data found.", file=sys.stderr)
        sys.exit(1)

    # Среднее время решения по всем файлам
    avg_solve_time = sum(solve_times) / len(solve_times)

    # Средний % времени для каждой функции
    avg_func = {name: sum(vals) / len(vals) for name, vals in func_times.items()}

    # Функция с наибольшим средним % времени
    best_func = max(avg_func, key=avg_func.get)
    best_avg = avg_func[best_func]

    print(f"Function consuming most average % time: {best_func} ({best_avg:.2f}%)")
    print(f"Average solving time across all files: {avg_solve_time:.3f} seconds")


if __name__ == "__main__":
    main()
