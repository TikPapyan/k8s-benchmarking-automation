#!/usr/bin/env python3

import pathlib

from logg import logger

def clean_logs(log_dir_path, pod_name=None):
    log_dir = pathlib.Path(log_dir_path)
    if not log_dir.exists():
        logger.warning(f"{log_dir_path} doesn't exist")
        return

    for log_file in log_dir.glob('*.log'):
        if pod_name is None or log_file.name.startswith(pod_name):
            log_file.unlink()
            logger.debug(f"Deleted log file {log_file.name}")
