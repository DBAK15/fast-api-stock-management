import logging
import os


def setup_logger(logger_name: str, log_file: str = "app.log", level=logging.INFO):
    """
    Configure and return a logger with file and console handlers.

    :param logger_name: Name of the logger
    :param log_file: Log file name in 'logs' directory
    :param level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    :return: Configured logger
    """
    # Create logs directory if it doesn't exist
    log_directory = "logs"
    os.makedirs(log_directory, exist_ok=True)

    # Get or create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Remove existing handlers to prevent duplicates
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # Log formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler (sans rotation)
    file_handler = logging.FileHandler(
        filename=os.path.join(log_directory, log_file),
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # Console handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
