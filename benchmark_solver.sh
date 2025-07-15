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
# Очищаем старые данные профилирования
rm -f "$PROFILE_PREFIX".* "$BENCH_DIR"/gmon.sum

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

    # Объединяем профили текущего запуска
    for gmon_file in "$PROFILE_PREFIX".*; do
      [ -f "$gmon_file" ] || continue
      echo " [DEBUG] merge $gmon_file" >&2
      if [ -f "$BENCH_DIR/gmon.sum" ]; then
        gprof -s "$SOLVER" "$BENCH_DIR/gmon.sum" "$gmon_file"
      else
        gprof -s "$SOLVER" "$gmon_file"
      fi
      mv gmon.sum "$BENCH_DIR/gmon.sum"
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
if [ -f "$BENCH_DIR/gmon.sum" ]; then
  {
    printf "Average solving time for %d CNFs: %.3f seconds\n\n" "$count" "$average"
    echo "Top 5 functions:"
    gprof "$SOLVER" "$BENCH_DIR/gmon.sum" | \
      awk 'BEGIN{head=0;count=0} /^Flat profile/ {head=1;print;getline;getline;print;next} head && count<5 {print;count++}'
  } > "$report_file"
  echo " [*] Profile saved to $report_file"
  rm -f "$BENCH_DIR/gmon.sum"
else
  echo " [!] gprof data not found"
fi
