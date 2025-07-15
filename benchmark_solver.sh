#!/bin/bash

N_THREADS=2

if [ "$#" -ne 2 ]; then
  echo " [!] Usage: $0 <solver_path> <cnf_folder>"
  exit 1
fi

SOLVER="$1"
CNF_FOLDER="$2"

# Каталог для сохранения итоговых отчётов
BENCH_DIR="benchmarks"
mkdir -p "$BENCH_DIR"

# Префикс для файлов профилирования
PROFILE_PREFIX="$BENCH_DIR/gmon"
# Временный файл для хранения промежуточных данных о функциях
TMP_FUNCS="$BENCH_DIR/tmp_profile.txt"
# Очищаем старые данные профилирования
rm -f "$PROFILE_PREFIX".* "$BENCH_DIR"/gmon.sum "$TMP_FUNCS"

total_time=0
count=0

for cnf_file in "$CNF_FOLDER"/*.cnf; do
  if [ -f "$cnf_file" ]; then
    echo " [*] Solving: $cnf_file"
    start=$(date +%s.%N)

    GMON_OUT_PREFIX="$PROFILE_PREFIX" "$SOLVER" "$cnf_file" --nThreads="$N_THREADS" > /dev/null

    end=$(date +%s.%N)

    # Защита от пустых значений
    if [[ -z "$start" || -z "$end" ]]; then
      echo " [!] Timing error for $cnf_file"
      continue
    fi

    # Приводим к числам с ведущим нулем, если нужно
    elapsed=$(awk "BEGIN {print $end - $start}")
    total_time=$(awk "BEGIN {print $total_time + $elapsed}")
    echo " [+] Elapsed $elapsed sec"
    count=$((count + 1))

    # Сохраняем топ-5 функций текущего запуска
    for gmon_file in "$PROFILE_PREFIX".*; do
      [ -f "$gmon_file" ] || continue
      echo " [DEBUG] profile $gmon_file" >&2
      gprof -b -p "$SOLVER" "$gmon_file" \
        | awk 'NR>=6 {print $3, $7}' | head -n 5 >> "$TMP_FUNCS"
      rm -f "$gmon_file"
    done

  fi
done

if [ "$count" -eq 0 ]; then
  echo " [!] No .cnf files found in $CNF_FOLDER"
  exit 2
fi

average=$(awk "BEGIN {print $total_time / $count}")
printf "\n Average solving time for %d CNFs: %.3f seconds\n" "$count" "$average"

report_file="$BENCH_DIR/benchmark_$(date +%Y.%m.%d_%H:%M:%S).txt"

# Формируем итоговый отчёт
if [ -s "$TMP_FUNCS" ]; then
  {
    printf "Average solving time for %d CNFs: %.3f seconds\n\n" "$count" "$average"
    echo "Top 5 functions:"
    awk '{time[$2]+=$1; cnt[$2]++} END {for(f in time) printf "%.6f %s\n", time[f]/cnt[f], f}' "$TMP_FUNCS" \
      | sort -nr | head -n 5
  } > "$report_file"
  echo " [*] Profile saved to $report_file"
  rm -f "$TMP_FUNCS"
else
  echo " [!] gprof data not found"
fi
