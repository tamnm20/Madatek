# =============================================================================
# modules/pending_queue.py — Quản lý hàng chờ upload FTP
# =============================================================================

import json
import os
import logging
import config

logger = logging.getLogger(__name__)


def _load():
    if not os.path.exists(config.PENDING_FILE):
        return []
    try:
        with open(config.PENDING_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Lỗi đọc pending queue: %s", e)
        return []


def _save(queue):
    try:
        tmp = config.PENDING_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(queue, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, config.PENDING_FILE)
    except Exception as e:
        logger.error("Lỗi ghi pending queue: %s", e)


def add(filepath):
    queue = _load()
    if filepath not in queue:
        queue.append(filepath)
        _save(queue)


def get_all():
    return _load()


def remove(filepath):
    queue = _load()
    if filepath in queue:
        queue.remove(filepath)
        _save(queue)


def count():
    return len(_load())
