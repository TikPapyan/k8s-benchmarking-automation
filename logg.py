#!/usr/bin/env python3

import os
import logging

LOG_DIR = "/var/log/scylla/bench"
logger = logging.getLogger('BenchLogger')

class LevelSpecificLogFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno == self.level

def setup_logging():
    log_level_str = os.getenv('LOG_LEVEL', 'INFO')
    log_level = getattr(logging, log_level_str.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError(f'Invalid log level: {log_level_str}')

    logger.setLevel(log_level)
    logger.handlers.clear()

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    def setup_handler(level, filename):
        handler = logging.FileHandler(os.path.join(LOG_DIR, filename))
        handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        handler.addFilter(LevelSpecificLogFilter(level))
        logger.addHandler(handler)

    setup_handler(logging.INFO, 'info.log')
    setup_handler(logging.WARNING, 'warning.log')
    setup_handler(logging.ERROR, 'error.log')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

