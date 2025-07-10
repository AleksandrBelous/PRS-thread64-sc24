#!/bin/bash

N_THREADS=2

if [ "$#" -ne 2 ]; then
  echo " [!] Usage: $0 <solver_path> <cnf_folder>"
  exit 1
fi

SOLVER="$1"
CNF_FOLDER="$2"

total_time=0
count=0

for cnf_file in "$CNF_FOLDER"/*.cnf; do
  if [ -f "$cnf_file" ]; then
    echo " [*] Solving: $cnf_file"
    start=$(date +%s.%N)

    "$SOLVER" "$cnf_file" --nThreads="$N_THREADS" > /dev/null

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
  fi
done

if [ "$count" -eq 0 ]; then
  echo " [!] No .cnf files found in $CNF_FOLDER"
  exit 2
fi

average=$(awk "BEGIN {print $total_time / $count}")
printf "\n Average solving time for %d CNFs: %.3f seconds\n" "$count" "$average"
