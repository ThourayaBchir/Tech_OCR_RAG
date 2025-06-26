# utils/logging.py

import logging
from logging.handlers import RotatingFileHandler


def configure_logging(
    log_file: str = "app.log",
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
):
    """
    Configure root logger with a rotating file handler and console output.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # File handler
    fh = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    fh.setFormatter(logging.Formatter(fmt))
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(fmt))
    logger.addHandler(ch)
