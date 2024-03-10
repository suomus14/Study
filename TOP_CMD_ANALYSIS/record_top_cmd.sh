#!/bin/bash

# Below is an example of the execution command.
# nohup sh record_top_cmd.sh &

# Set the measurement interval. [sec]
interval=30

# The top command omits the display depending on the screen width,
# so it virtually increases the screen width.
export COLUMNS=600

cur_date=""
pre_date=""
log_file=""
dir_name="system_metrics"
log_name="top_cmd"

mkdir -p "$dir_name"

while true; do
    cur_date=$(date +"%Y-%m-%d")
    if [ "${cur_date}" != "${pre_date}" ]; then
        pre_date="$cur_date"
        log_file="${dir_name}/${log_name}_${cur_date}.log"
        echo "date info: ${cur_date}" > "$log_file"
        echo "" | tee -a "$log_file"
    fi

    echo "------------------------------" | tee -a "$log_file"
    echo "timestamp: $(date +"%Y/%m/%d %H:%M:%S")" | tee -a "$log_file"
    top -b -n 1 -c -o RES | tee -a "$log_file"
    echo "" | tee -a "$log_file"

    sleep $interval
done

