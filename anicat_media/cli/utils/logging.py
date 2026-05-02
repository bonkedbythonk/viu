import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ...core.constants import LOG_FILE

root_logger = logging.getLogger()
logger = logging.getLogger(__name__)


def setup_logging(log: bool | None) -> None:
    """Configures the application's logging based on CLI flags."""

    _setup_default_logger()
    if log:
        from rich.logging import RichHandler

        root_logger.addHandler(RichHandler())
        logger.info("Rich logging initialized.")


def _setup_default_logger(
    log_file_path: Path = LOG_FILE,
    max_bytes=10 * 1024 * 1024,  # 10mb
    backup_count=5,
    level=logging.DEBUG,
):
    root_logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - [%(process)d:%(thread)d] - %(levelname)-8s  - %(name)s - %(filename)s:%(lineno)d - %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
