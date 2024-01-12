#!/usr/bin/env python3

import subprocess
import os

from logg import logger


def run_command(command):
    logger.debug(f"Running command: {' '.join(command)}")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.stdout:
        logger.info(f"stdout: {result.stdout}")
    if result.stderr:
        logger.error(f"stderr: {result.stderr}")
    return result


def run_hw_metrics(log_dir, duration, remote_user, remote_ip, ssh_password):
    script_src_path = "hw.sh"
    remote_script_path = f"/tmp/{os.path.basename(script_src_path)}"
    remote_output_path = "/tmp/hw_output.txt"
    local_output_path = os.path.join(log_dir, "hw_output.txt")

    cleanup_command = f"rm -f {remote_script_path} {remote_output_path}"
    
    run_command(["sshpass", "-p", ssh_password, "ssh", "-o", "StrictHostKeyChecking=no", f"{remote_user}@{remote_ip}", cleanup_command])
    run_command(["sshpass", "-p", ssh_password, "scp", script_src_path, f"{remote_user}@{remote_ip}:{remote_script_path}"])
    run_command(["sshpass", "-p", ssh_password, "ssh", "-o", "StrictHostKeyChecking=no", f"{remote_user}@{remote_ip}", f"bash {remote_script_path} {duration}"])
    run_command(["sshpass", "-p", ssh_password, "scp", f"{remote_user}@{remote_ip}:{remote_output_path}", local_output_path])

    with open(local_output_path, 'r') as output_file:
        hardware_metrics = output_file.read()
    logger.info("---- Hardware Metrics Results ----\n")
    logger.info(f"\n\n{hardware_metrics}")


def parse_hardware_metrics(log_dir):
    hardware_metrics_file = os.path.join(log_dir, "hw_output.txt")
    hardware_metrics = {}

    try:
        with open(hardware_metrics_file, 'r') as file:
            for line in file:
                if "Average VRAM" in line:
                    hardware_metrics["VRAM"] = line.split(":")[1].strip()
                elif "Average RAM" in line:
                    hardware_metrics["RAM"] = line.split(":")[1].strip()
                elif "Average CPU" in line:
                    hardware_metrics["CPU"] = line.split(":")[1].strip()
                elif "Average GPU" in line:
                    hardware_metrics["GPU"] = line.split(":")[1].strip()
    except FileNotFoundError:
        logger.error(f"Hardware metrics file not found: {hardware_metrics_file}")

    return hardware_metrics