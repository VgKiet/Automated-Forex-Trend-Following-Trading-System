import logging
import os

os.makedirs("logs", exist_ok=True)

# =========================
# PYBOT LOGGER
# =========================

pybot_logger = logging.getLogger("pybot")
pybot_logger.setLevel(logging.DEBUG)

pybot_handler = logging.FileHandler(
    "logs/pybot.log",
    encoding="utf-8"
)

pybot_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
)

pybot_logger.addHandler(pybot_handler)

# =========================
# TRADE LOGGER
# =========================

trade_logger = logging.getLogger("trade")
trade_logger.setLevel(logging.INFO)

trade_handler = logging.FileHandler(
    "logs/trades.log",
    encoding="utf-8"
)

trade_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
)

trade_logger.addHandler(trade_handler)

# =========================
# ERROR LOGGER
# =========================

error_logger = logging.getLogger("error")
error_logger.setLevel(logging.WARNING)

error_handler = logging.FileHandler(
    "logs/errors.log",
    encoding="utf-8"
)

error_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
)

error_logger.addHandler(error_handler)

# =========================
# REPORT LOGGER
# =========================

report_logger = logging.getLogger("report")
report_logger.setLevel(logging.INFO)

report_handler = logging.FileHandler(
    "logs/report.log",
    encoding="utf-8"
)

report_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(message)s"
    )
)

report_logger.addHandler(report_handler)