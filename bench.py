#!/usr/bin/env python3

import os
import threading
import time

from calculations import *
from logg import logger, setup_logging
from k8s import capture_logs
from cleanup import clean_logs
from hw import run_hw_metrics
from deployment_processing import process_and_write_results

DEPLOYMENTS = ["rmd", "ids", "ptd", "tfa", "fds", "sfds", "snfds", "tds", "aod", "frs"]
LOG_DIR = "/var/log/scylla/bench"
SINGLE_RESULT_FILE_PATH = os.path.join(LOG_DIR, "single_results.csv")
COMBO_RESULT_FILE_PATH = os.path.join(LOG_DIR, "combo_results.csv")
DEPLOYMENT_CONDITION_TIMEOUT = 120

DURATION = int(os.getenv('DURATION', 60))
REMOTE_USER = os.getenv('REMOTE_USER', "scylla")
REMOTE_IP = os.getenv('REMOTE_IP', "192.168.11.203")
SSH_PASSWORD = os.getenv('SSH_PASSWORD', "$cy11a")


def main():
    try:
        clean_logs(LOG_DIR)
        setup_logging()

        logger.info(f"Starting benchmarking for {DURATION} seconds.")

        threads = []
        for deployment in DEPLOYMENTS:
            log_thread = threading.Thread(target=capture_logs, args=(deployment, DURATION, LOG_DIR))
            log_thread.start()
            threads.append(log_thread)

        hw_thread = threading.Thread(target=run_hw_metrics, args=(LOG_DIR, DURATION, REMOTE_USER, REMOTE_IP, SSH_PASSWORD))
        hw_thread.start()
        threads.append(hw_thread)

        for thread in threads:
            thread.join()

        logger.info("Hardware metrics collection completed.")
        logger.debug("Processing pod metrics.")
        process_and_write_results(LOG_DIR, DEPLOYMENTS, SINGLE_RESULT_FILE_PATH, COMBO_RESULT_FILE_PATH)

        while True:
            time.sleep(10)

    finally:
        logger.info("Cleaning up.")
        clean_logs(LOG_DIR)

if __name__ == "__main__":
    main()

