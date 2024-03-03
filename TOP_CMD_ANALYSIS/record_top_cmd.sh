#!/bin/bash

# Set the measurement interval. [sec]
interval=30

# The top command omits the display depending on the screen width,
# so it virtually increases the screen width.
export COLUMNS=400

cur_date=""
pre_date=""
log_file=""
dir_path="system_metrics"

mkdir -p "$dir_path"

while true; do
    cur_date=$(date +"%Y-%m-%d")
    if [ "$cur_date" != "$pre_date" ]; then
        pre_date="$cur_date"
        log_file="$dir_path/system_metrics_$cur_date.log"
        echo "date info: $cur_date" > "$log_file"
    fi

    echo "" | tee -a "$log_file"
    echo "------------------------------" | tee -a "$log_file"
    echo "timestamp: $(date +"%Y/%m/%d %H:%M:%S")" | tee -a "$log_file"
    top -b -n 1 -c -o RES | tee -a "$log_file"

    sleep $interval
done
