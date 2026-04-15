import logging
import sys
from datetime import datetime
from pathlib import Path


_RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
_LOGS_DIR = Path(__file__).resolve().parent / "logs"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE_PATH = _LOGS_DIR / f"run_{_RUN_TIMESTAMP}.log"
_LOG_FORMAT = "[%(asctime)s] %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_LOGGER = logging.getLogger("daily_mail_summary")
_LOGGER.setLevel(logging.INFO)
_LOGGER.propagate = False


def _configure_logger():
    if _LOGGER.handlers:
        return

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _LOGGER.addHandler(console_handler)

    try:
        file_handler = logging.FileHandler(_LOG_FILE_PATH, encoding="utf-8")
        file_handler.setFormatter(formatter)
        _LOGGER.addHandler(file_handler)
    except OSError:
        # Do not fail the run if filesystem logging is unavailable.
        pass


_configure_logger()


def log(message):
    """Logs a message to console and run log file."""
    _LOGGER.info(str(message))
