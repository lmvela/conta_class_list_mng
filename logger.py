import os
import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = "./log"
LOG_FILE = os.path.join(LOG_DIR, 'main.log')

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def get_logger(name='conta_logger'):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.ERROR)
        handler = RotatingFileHandler(LOG_FILE, maxBytes=2*1024*1024, backupCount=3, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger
