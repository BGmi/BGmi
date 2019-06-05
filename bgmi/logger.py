import os
import sys
from logging import (
    BASIC_FORMAT, DEBUG, INFO, FileHandler, Formatter, Logger, StreamHandler, getLevelName,
    getLogger
)

from bgmi import config


def get_logger() -> Logger:
    log_level = config.LOG_LEVEL
    log_level = log_level.upper()
    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
        print('log level invalid, will use default log level info')
        log_level = 'INFO'
    _logger = getLogger('bgmi')
    _logger.setLevel(log_level)

    stdout = StreamHandler(sys.stdout)
    stdout.setFormatter(Formatter('%(message)s'))
    if os.getenv('DEBUG'):
        stdout.setLevel(DEBUG)
    else:
        stdout.setLevel(INFO)
    _logger.addHandler(stdout)

    try:
        h = FileHandler(config.LOG_PATH, 'a+', 'utf-8')
        h.setFormatter(Formatter(BASIC_FORMAT))
        h.setLevel(getLevelName(log_level))
        _logger.addHandler(h)
        if log_level == 'DEBUG':
            orm_logger = getLogger('peewee')
            orm_logger.setLevel(DEBUG)
            orm_logger.addHandler(h)
    except IOError:
        _logger.info("Can't create log file, log to file is disabled.")

    return _logger


logger = get_logger()
