# logging_config.py
import logging
import sys
import os

_CONFIGURED = False
ALLOWED_PREFIXES = ("agent", "perception", "planner", "executor", "verifier")

class OnlyMyLogsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.name.startswith(ALLOWED_PREFIXES)
    
def setup_logging(level: str = "INFO", log_file: str = None):
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, level.upper()))
    console.setFormatter(fmt)
    root.addHandler(console)

    if log_file:
        log_dir = os.path.dirname(os.path.abspath(log_file))
        os.makedirs(log_dir, exist_ok=True)
        fileh = logging.FileHandler(log_file, encoding="utf-8")
        fileh.setLevel(logging.DEBUG)
        fileh.setFormatter(fmt)
        fileh.addFilter(OnlyMyLogsFilter())
        root.addHandler(fileh)