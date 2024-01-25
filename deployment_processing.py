#!/usr/bin/env python3

import os
import time
from glob import glob
import csv

from calculations import *
from logg import logger
from hw import parse_hardware_metrics


deployments_mapping = {
    'ptd': [calculate_average_load],
    'ids': [calculate_average_load, calculate_ids_motion],
    'rmd': [calculate_average_load],
    'aod': [calculate_average_load],
    'tfa': [calculate_num_samples],
    'fds': [calculate_queue_size],
    'sfds': [calculate_queue_size],
    'snfds': [calculate_queue_size],
    'tds': [calculate_queue_size],
    'frs': [calculate_fps]
}


def write_csv_header(csvwriter, results_file, header):
    if not os.path.exists(results_file) or os.path.getsize(results_file) == 0:
        csvwriter.writerow(header)


def calculate_and_log_metrics(deployment_name, log_file_path, log_dir):
    metrics = {}
    for calculate in deployments_mapping[deployment_name]:
        result_type = calculate.__name__
        
        if result_type == "calculate_ids_motion" and deployment_name == "ids":
            info_log_files = glob(os.path.join(log_dir, f"info-{deployment_name}-*.log"))
            if info_log_files:
                info_log_file_path = info_log_files[0]
                result = calculate(info_log_file_path)
            else:
                result = ""
        else:
            result = calculate(log_file_path)

        metrics[result_type] = result if result is not None else ""

        if result is not None:
            if isinstance(result, dict):
                formatted_result = json.dumps(result, indent=2)
                logger.info(f"Result for {deployment_name}: \n\n{formatted_result}\n\n")
            else:
                logger.info(f"Result for {deployment_name}: {result}\n")

    return metrics


def process_single_deployments(csvwriter, log_dir, deployments, hardware_metrics):
    logger.debug("Starting process_single_deployments function.")

    log_files = glob(os.path.join(log_dir, "*.log"))
    for log_file_path in log_files:
        file_name = os.path.basename(log_file_path)
        if file_name.startswith(tuple(deployments)):
            logger.debug(f"Processing pod log file: {log_file_path}")
            deployment_name = file_name.split('-')[0]

            with open(log_file_path, 'r') as log_file:
                logs = log_file.read()

            camera_number = extract_camera_number(logs, deployment_name)
            logger.info(f"{deployment_name} camera number: {camera_number}")
            camera_info = camera_number if camera_number else ""

            row = [deployment_name, camera_info] + [hardware_metrics.get(k, "") for k in ["VRAM", "RAM", "CPU", "GPU"]] + [""] * 5

            if deployment_name in deployments_mapping:
                metrics = calculate_and_log_metrics(deployment_name, log_file_path, log_dir)
                row[6:] = [metrics.get("calculate_average_load", ""), 
                           metrics.get("calculate_num_samples", ""), 
                           metrics.get("calculate_queue_size", ""), 
                           metrics.get("calculate_fps", ""), 
                           metrics.get("calculate_ids_motion", "")]

            csvwriter.writerow(row)


def process_combo_deployments(csvwriter, log_dir, deployments, hardware_metrics, combo_header):
    logger.debug("Starting process_combo_deployments function.")

    row = [hardware_metrics.get("VRAM", ""),
           hardware_metrics.get("RAM", ""),
           hardware_metrics.get("CPU", ""),
           hardware_metrics.get("GPU", "")] + [""] * (len(combo_header) - 4)

    family_column_indices = {
        "ids": {"Camera Number": 4, "Server Load (%)": 5, "Motion Count": 6},
        "ptd": {"Camera Number": 7, "Server Load (%)": 8},
        "tfa": {"Camera Number": 9, "Num Samples": 10},
        "ads": {"Camera Number": 11, "Queue Size": 12},
        "frs": {"Camera Number": 13, "FPS": 14},
        "aod": {"Camera Number": 15, "Server Load (%)": 16},
        "fds": {"Camera Number": 11, "Queue Size": 12},
    }

    metric_name_to_column_title = {
        'calculate_average_load': 'Server Load (%)',
        'calculate_ids_motion': 'Motion Count',
        'calculate_queue_size': 'Queue Size',
        'calculate_fps': 'FPS',
        'calculate_num_samples': 'Num Samples'
    }

    for deployment_name in deployments:
        log_file_pattern = f"{deployment_name}-*.log"
        log_files = glob(os.path.join(log_dir, log_file_pattern))
        log_file_path = log_files[0] if log_files else None

        if log_file_path:
            with open(log_file_path, 'r') as log_file:
                logs = log_file.read()

            metrics = calculate_and_log_metrics(deployment_name, log_file_path, log_dir)
            camera_number = extract_camera_number(logs, deployment_name)
            logger.info(f"{deployment_name} camera number: {camera_number}")
            metrics["Camera Number"] = camera_number

            column_mapping = family_column_indices.get(deployment_name, {})
            for metric_function_name, column_title in metric_name_to_column_title.items():
                metric_value = metrics.get(metric_function_name, "")
                if column_title in column_mapping:
                    column_index = column_mapping[column_title]
                    row[column_index] = metric_value
                    logger.debug(f"Assigned {column_title} ({metric_value}) to column {column_index}")

            if "Camera Number" in column_mapping:
                camera_number_column_index = column_mapping["Camera Number"]
                row[camera_number_column_index] = camera_number

    csvwriter.writerow(row)


def process_and_write_results(log_dir, deployments, single_results_file, combo_results_file):
    single_header = ["Deployment Name", "Camera Number", "VRAM (MB)", "RAM (GB)", "CPU (%)", "GPU (%)", 
                "Server Load (%)", "Num Samples", "Queue Size", "FPS", "Motion Count"]

    combo_header = ["VRAM (MB)", "RAM (GB)", "CPU (%)", "GPU (%)", 
                    "ids - Camera Number", "ids - Server Load (%)", "ids - Motion Count", 
                    "ptd - Camera Number", "ptd - Server Load (%)",
                    "tfa - Camera Number", "tfa - Num Samples", 
                    "ads - Camera Number", "ads - Queue Size",
                    "frs - Camera Number", "frs - FPS",
                    "aod - Camera Number", "aod - Server Load (%)"]

    hardware_metrics = parse_hardware_metrics(log_dir)

    log_files = glob(os.path.join(log_dir, "*.log"))

    running_deployments = [d for d in deployments if any(log_file.startswith(os.path.join(log_dir, d)) for log_file in log_files)]
    num_running_deployments = len(running_deployments)

    logger.debug(f"Found {num_running_deployments} running deployments: {running_deployments}")

    if num_running_deployments > 1:
        with open(combo_results_file, 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            write_csv_header(csvwriter, combo_results_file, combo_header)
            process_combo_deployments(csvwriter, log_dir, running_deployments, hardware_metrics, combo_header)
    elif num_running_deployments == 1:
        with open(single_results_file, 'a', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            write_csv_header(csvwriter, single_results_file, single_header)
            process_single_deployments(csvwriter, log_dir, running_deployments, hardware_metrics)
    else:
        logger.debug("No deployments are currently running.")

    logger.debug("Finished processing and writing results.")
