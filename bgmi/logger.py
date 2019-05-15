import logging
import os
import sys

from bgmi import config


def get_logger():
    log_level = config.LOG_LEVEL
    log_level = log_level.upper()
    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
        print('log level invalid, will use default log level info')
        log_level = 'INFO'
    _logger = logging.getLogger('bgmi')
    if not os.getenv('UNITTEST'):
        _logger.addHandler(logging.StreamHandler(sys.stdout))
    try:
        h = logging.FileHandler(config.LOG_PATH, 'a+', 'utf-8')
        h.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
        h.setLevel(logging.getLevelName(log_level))
        _logger.addHandler(h)
        if log_level == 'DEBUG':
            orm_logger = logging.getLogger('peewee')
            orm_logger.setLevel(logging.DEBUG)
            orm_logger.addHandler(h)
    except IOError as e:
        print(e)
        _logger.info("Can't create log file, log to file is disabled.")

    return _logger


logger = get_logger()
