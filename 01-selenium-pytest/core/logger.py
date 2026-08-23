"""Merkezi loglama.

KARSILASTIRMA NOTU:
    Robot Framework her adimi otomatik olarak log.html icine yazar; hicbir sey
    yazmaniza gerek yoktur. Selenium'da "ne olup bittigini" gormek icin logu
    kendiniz kurar ve her page object metodunda kendiniz cagirirsiniz.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

_CONFIGURED = False
_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-28s | %(message)s"


def configure_logging(log_dir: Path, level: int = logging.INFO) -> Path:
    """Konsol + dosya handler'larini bir kez kurar, log dosyasi yolunu doner."""
    global _CONFIGURED

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"

    if _CONFIGURED:
        return log_file

    root = logging.getLogger("suite")
    root.setLevel(level)
    root.propagate = False

    formatter = logging.Formatter(_FORMAT, datefmt="%H:%M:%S")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    # Selenium'un kendi DEBUG gurultusunu kis
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    _CONFIGURED = True
    return log_file


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"suite.{name}")
