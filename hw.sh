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

    echo "Debug: CPU $local_cpu, GPU $local_gpu, VRAM $local_vram, RAM $local_ram" >> gpu.log

    if [[ ! $local_cpu =~ ^[0-9]+([.][0-9]+)?$ ]]; then local_cpu=0; fi
    if [[ ! $local_gpu =~ ^[0-9]+([.][0-9]+)?$ ]]; then local_gpu=0; fi
    if [[ ! $local_vram =~ ^[0-9]+([.][0-9]+)?$ ]]; then local_vram=0; fi
    if [[ ! $local_ram =~ ^[0-9]+([.][0-9]+)?$ ]]; then local_ram=0; fi

    total_cpu=$(echo "$total_cpu + $local_cpu" | bc)
    total_gpu=$(echo "$total_gpu + $local_gpu" | bc)
    total_vram=$(echo "$total_vram + $local_vram" | bc)
    total_ram=$(echo "$total_ram + $local_ram" | bc)
    
    count=$((count + 1))
done

average_vram=$(echo "scale=$decimal_places; $total_vram / $count" | bc)
average_ram=$(echo "scale=$decimal_places; $total_ram / $count" | bc)
average_cpu=$(echo "scale=$decimal_places; $total_cpu / $count" | bc)
average_gpu=$(echo "scale=$decimal_places; $total_gpu / $count" | bc)

echo "Average VRAM: $average_vram MB" >> "$output_file"
echo "Average RAM: $average_ram GB" >> "$output_file"
echo "Average CPU: $average_cpu%" >> "$output_file"
echo "Average GPU: $average_gpu%" >> "$output_file"

rm gpu.log