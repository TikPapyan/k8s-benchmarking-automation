#!/usr/bin/env python3

import re
import json

from logg import logger

NS_STEP = 10


def read_file_lines(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.readlines()
    except FileNotFoundError:
        logger.error(f"File '{file_path}' not found.")
    except IOError as io_err:
        logger.error(f"I/O error reading file '{file_path}': {io_err}")
    except Exception as e:
        logger.error(f"Unexpected error processing file '{file_path}': {e}")
    return None


def calculate_average_load(log_file_path):
    logger.debug(f"Calculating average load for {log_file_path}")
    lines = read_file_lines(log_file_path)

    server_loads = [int(re.sub('%', '', m.group(0))) for line in lines if (m := re.search(r'\d*%', line))]

    if server_loads:
        average_server_load = sum(server_loads) / len(server_loads)
        return f"{round(average_server_load, 2)}% ({len(server_loads)})"
    else:
        logger.error(f'No server load data found in {log_file_path}')
        return "error"


def calculate_ids_motion(info_log_file):
    logger.debug(f"Calculating motion count for {info_log_file}")

    lines = read_file_lines(info_log_file)
    if lines is None:
        return "error"

    pattern = re.compile(r'\[.*\] Number of motion alerts from camera: \[(.*?)\](\d+)')
    camera_data = {}

    for line in lines:
        match = pattern.search(line)
        if match:
            camera, count = match.groups()
            count = int(count)
            camera_data.setdefault(camera, []).append(count)

    if not camera_data:
        logger.debug(f"No motion data found in file {info_log_file}")
        return None

    averages = {camera: sum(counts) / len(counts) for camera, counts in camera_data.items()}
    sum_of_averages = sum(averages.values())
    return round(sum_of_averages)


def sort_num_samples(hash_map) -> dict:
    new_map = {"num_samples": {}}
    temp_sorting = []
    
    for key in hash_map["num_samples"].keys():
        temp_sorting.append(key)
    
    temp_sorting.sort(key=lambda x: int(x.split(" - ")[0]))
    
    for i in temp_sorting:
        avg_load = round(sum(hash_map["num_samples"][i]) / len(hash_map["num_samples"][i]), 2)
        count = len(hash_map["num_samples"][i])
        new_map["num_samples"].update({i: f"{avg_load}% ({count})"})
    
    return new_map


def calculate_num_samples(log_file_path):
    logger.debug(f"Calculating number of samples for {log_file_path}")
    
    lines = read_file_lines(log_file_path)
    if lines is None:
        return "error"

    results = {"num_samples": {}}
    num_samples_sum = 0
    num_samples_count = 0
    load_pattern = re.compile(r"Server load of inference (\d*)%")
    sample_pattern = re.compile("Num samples:.\d*")

    for line in lines:
        temp_search = load_pattern.search(line.strip())
        if temp_search:
            temp_value = int(temp_search.group(1))
            if num_samples_count > 0:
                num_samples_chunk_avg = num_samples_sum / num_samples_count
                num_samples_sum = 0
                num_samples_count = 0

                for i in range(0, 20):
                    if i * NS_STEP <= num_samples_chunk_avg < (i + 1) * NS_STEP:
                        range_key = f"{i*NS_STEP} - {(i+1)*NS_STEP}"
                        results["num_samples"].setdefault(range_key, []).append(temp_value)

        temp_search = sample_pattern.search(line.strip())
        if temp_search:
            temp_search_num = float(temp_search.group().split(": ")[1])
            num_samples_sum += temp_search_num
            num_samples_count += 1

    formatted_results = {range_key: f"{sum(load_values) / len(load_values):.2f}% ({len(load_values)})"
                         for range_key, load_values in results["num_samples"].items()}

    return json.dumps(formatted_results, indent=2)


def calculate_queue_size(log_file_path):
    logger.debug(f"Calculating queue size for {log_file_path}")
    lines = read_file_lines(log_file_path)
    if lines is None:
        return "error"

    queue_sizes = [float(match.group(1)) for line in lines if (match := re.search(r'Inference queue size: (\d+(?:\.\d+)?)', line))]

    if queue_sizes:
        average_queue = sum(queue_sizes) / len(queue_sizes)
        return f"{average_queue} ({len(queue_sizes)})"
    else:
        logger.error(f'No queue size data found in {log_file_path}')
        return "error"
    

def calculate_fps(log_file_path):
    logger.debug(f"Calculating FPS for {log_file_path}")
    lines = read_file_lines(log_file_path)
    if lines is None:
        return "error"

    fps_values = [float(match.group(1)) for line in lines if (match := re.search(r'FPS:(\d+\.\d+)', line))]

    if fps_values:
        average_fps = sum(fps_values) / len(fps_values)
        return f"{average_fps} ({len(fps_values)})"
    else:
        logger.error(f'No FPS data found in {log_file_path}')
        return "error"


def extract_camera_number(logs, deployment_type):
    camera_number = None
    
    if deployment_type in ['ptd', 'rmd', 'aod']:
        match = re.search(r'Number of cameras: (\d+)', logs)
        if match:
            camera_number = match.group(1)
    elif deployment_type in ['fds', 'snfds', 'sfds', 'tds']:
        match = re.search(r'Total number of cameras:(\d+)', logs)
        if match:
            camera_number = match.group(1)
    elif deployment_type == 'ids':
        match = re.search(r'Batch size: (\d+)', logs)
        if match:
            camera_number = match.group(1)
    elif deployment_type == 'tfa':
        match = re.search(r'Batch size: (\d+)', logs)
        if match:
            camera_number = match.group(1)
            camera_number = camera_number * 2

    return camera_number
