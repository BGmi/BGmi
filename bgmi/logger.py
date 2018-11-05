import os
import logging
import sys
from bgmi.config import LOG_PATH


def get_logger():
    log_level = os.environ.get('BGMI_LOG') or 'ERROR'
    log_level = log_level.upper()
    if log_level not in ['DEBUG', 'INFO', "WARNING", "ERROR"]:
        print('log level error, doing nothing and exit')
        exit(1)
    logger = logging.getLogger('BGmi')
    try:
        h = logging.FileHandler(LOG_PATH, 'a+', 'utf-8')
        fs = logging.BASIC_FORMAT
        fmt = logging.Formatter(fs)
        h.setFormatter(fmt)
        logger.addHandler(h)
        logger.setLevel(logging.getLevelName(log_level))
        if log_level == "DEBUG" and not os.environ.get("TRAVIS_CI", False):
            logger.addHandler(logging.StreamHandler(sys.stdout))
            logger.debug("enable debug logger")
    except IOError as e:
        print(e)
        logging.basicConfig(stream=sys.stdout, level=logging.getLevelName(log_level))
    return logger


logger = get_logger()
