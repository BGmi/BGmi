import os
import logging
import sys
from bgmi.config import LOG_PATH


def get_logger():
    log_level = os.environ.get('BGMI_LOG') or 'INFO'
    log_level = log_level.upper()
    if log_level not in ['DEBUG', 'INFO', "WARNING", "ERROR"]:
        print('log level error, doing nothing and exit')
        exit(1)
    logger = logging.getLogger('BGmi')
    try:
        h = logging.FileHandler(LOG_PATH, 'a+', 'utf-8')
        fmt = logging.Formatter(logging.BASIC_FORMAT)
        h.setFormatter(fmt)
        logger.addHandler(h)
        logger.setLevel(logging.getLevelName(log_level))
    except IOError as e:
        print("can't create log file, disable logger. Ignore this if you run bgmi at first time.")
    return logger


logger = get_logger()
