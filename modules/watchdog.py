# =============================================================================
# modules/watchdog.py — Giám sát tài nguyên hệ thống
# =============================================================================

import os
import shutil
import logging
from modules import pending_queue
import config

logger = logging.getLogger(__name__)


def check_disk():
    try:
        path = config.DATA_DIR if os.path.exists(config.DATA_DIR) else "."
        usage = shutil.disk_usage(path)
        free_mb = usage.free / (1024 * 1024)
        if free_mb < config.DISK_MIN_FREE_MB:
            logger.warning("DISK SẮP ĐẦY! Còn %.0f MB (ngưỡng: %d MB)",
                           free_mb, config.DISK_MIN_FREE_MB)
        else:
            logger.debug("Disk OK: còn %.0f MB", free_mb)
    except Exception as e:
        logger.error("Lỗi kiểm tra disk: %s", e)


def check_memory():
    try:
        import psutil
        mem = psutil.virtual_memory()
        if mem.percent > config.MEMORY_WARN_PERCENT:
            logger.warning("RAM CAO! Đang dùng %.1f%% (ngưỡng: %d%%)",
                           mem.percent, config.MEMORY_WARN_PERCENT)
        else:
            logger.debug("RAM OK: %.1f%%", mem.percent)
    except ImportError:
        pass
    except Exception as e:
        logger.error("Lỗi kiểm tra RAM: %s", e)


def check_pending():
    n = pending_queue.count()
    if n > 0:
        logger.info("Pending queue: %d file chờ upload", n)


def run_all():
    check_disk()
    check_memory()
    check_pending()
