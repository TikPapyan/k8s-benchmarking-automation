#!/bin/bash

duration=$1
interval=1
decimal_places=2

total_vram=0
total_ram=0
total_cpu=0
total_gpu=0
count=0

output_file="/tmp/hw_output.txt"

> gpu.log

for ((i=0; i<=$duration; i+=$interval))
do
    local_cpu=$(sar -u $interval 1 | awk 'NR>3 {sum += 100 - $NF; local_count++} END {if (local_count > 0) print sum/local_count; else print 0}')
    local_gpu=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | awk '{sum += $1; local_count++} END {if (local_count > 0) print sum/local_count; else print 0}')
    local_vram=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | awk '{sum += $1; local_count++} END {if (local_count > 0) print sum/local_count; else print 0}')
    local_ram=$(free -m | awk '/^Mem/ {print $3 / 1024}')

    total_cpu=$(awk "BEGIN {print $total_cpu + $local_cpu}")
    total_gpu=$(awk "BEGIN {print $total_gpu + $local_gpu}")
    total_vram=$(awk "BEGIN {print $total_vram + $local_vram}")
    total_ram=$(awk "BEGIN {print $total_ram + $local_ram}")
    
    count=$((count + 1))

    echo "VRAM: $local_vram MB, GPU: $local_gpu%" >> gpu.log
done

average_vram=$(awk "BEGIN {rounded = sprintf(\"%.${decimal_places}f\", $total_vram / $count); print rounded}")
average_ram=$(awk "BEGIN {rounded = sprintf(\"%.${decimal_places}f\", $total_ram / $count); print rounded}")
average_cpu=$(awk "BEGIN {rounded = sprintf(\"%.${decimal_places}f\", $total_cpu / $count); print rounded}")
average_gpu=$(awk "BEGIN {rounded = sprintf(\"%.${decimal_places}f\", $total_gpu / $count); print rounded}")

echo "Average VRAM: $average_vram MB" >> "$output_file"
echo "Average RAM: $average_ram GB" >> "$output_file"
echo "Average CPU: $average_cpu%" >> "$output_file"
echo "Average GPU: $average_gpu%" >> "$output_file"

rm gpu.log
