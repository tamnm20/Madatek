# =============================================================================
# modules/settings_manager.py — Đọc/ghi settings.json
# Cache settings trong memory, chỉ đọc file khi cần thiết
# =============================================================================

import json
import os
import logging

logger = logging.getLogger(__name__)

SETTINGS_FILE = "settings.json"

DEFAULTS = {
    "gateway_id":       "000000",
    "device_id":        "000000",
    "ftp_host":         "0.0.0.0",
    "ftp_port":         21,
    "ftp_user":         "user",
    "ftp_pass":         "pass",
    "mqtt_host":        "0.0.0.0",
    "mqtt_port":        1883,
    "mqtt_user":        "user",
    "mqtt_pass":        "pass",
    "mqtt_topic":       "iot/admin/water/telemetry",
    "interval_seconds": 300,
    "interval_display": 1,
}

_cache = None


def load():
    global _cache
    if _cache is not None:
        return _cache
    _cache = _load_from_file()
    return _cache


def reload():
    global _cache
    _cache = _load_from_file()
    return _cache


def _load_from_file():
    if not os.path.exists(SETTINGS_FILE):
        logger.warning("Không tìm thấy settings.json, dùng giá trị mặc định!")
        return dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key, val in DEFAULTS.items():
            if key not in data:
                data[key] = val
        logger.info("Đã đọc settings.json")
        return data
    except Exception as e:
        logger.error("Lỗi đọc settings.json: %s", e)
        return dict(DEFAULTS)


def save(settings):
    global _cache
    try:
        tmp = SETTINGS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, SETTINGS_FILE)
        _cache = dict(settings)
        logger.info("Đã lưu settings.json")
        return True
    except Exception as e:
        logger.error("Lỗi ghi settings.json: %s", e)
        return False


def get(key, default=None):
    return load().get(key, default)
