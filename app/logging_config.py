import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | "
    "%(name)s | %(filename)s:%(lineno)d | %(message)s"
)

def setup_logging():
    logging.basicConfig(level=logging.INFO)

    formatter = logging.Formatter(LOG_FORMAT)

    # App log (all logs)
    app_handler = RotatingFileHandler(
        f"{LOG_DIR}/app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8" 
    )
    app_handler.setFormatter(formatter)
    app_handler.setLevel(logging.INFO)

    # Error log (only errors)
    error_handler = RotatingFileHandler(
        f"{LOG_DIR}/error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8" 
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    root_logger = logging.getLogger()
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)


