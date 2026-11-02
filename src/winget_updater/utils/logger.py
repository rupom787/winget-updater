"""Logging utility configured for file and console output."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

LOGGER_NAME = "winget_updater"
DEFAULT_LOG_FILE = "winget_updater.log"


def get_default_log_path() -> Path:
    """Returns the default log file path in App directory or LocalAppData."""
    if hasattr(sys, "frozen"):
        return Path(sys.executable).resolve().parent / DEFAULT_LOG_FILE
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        log_dir = Path(local_app_data) / "WingetUpdater"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / DEFAULT_LOG_FILE
    return Path.cwd() / DEFAULT_LOG_FILE


def setup_logger(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """Initializes and configures the centralized logger."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (safely handle windowed exe where stdout may be None)
    if sys.stdout is not None:
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        except Exception:
            pass

    # File handler
    if log_file is None:
        log_file = get_default_log_path()
    
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Failed to create file logger at {log_file}: {e}")

    return logger


def get_logger() -> logging.Logger:
    """Returns the logger instance, ensuring setup has been run."""
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        return setup_logger()
    return logger

