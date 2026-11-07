# =============================================================================
# modules/mqtt_publisher.py — Publish data lên MQTT broker
# Store-and-forward: publish thất bại → lưu vào pending_mqtt.json → retry sau
# Timeout thật sự bằng socket, log đầy đủ
# =============================================================================

import json
import os
import logging
import socket
import time
import random
from modules import settings_manager

logger = logging.getLogger(__name__)

PENDING_MQTT_FILE = "pending_mqtt.json"
CONNECT_TIMEOUT   = 5
PUBLISH_TIMEOUT   = 5

# Delay giữa các payload khi retry (giây)
RETRY_DELAY_MIN = 2
RETRY_DELAY_MAX = 3


def _load_pending():
    if not os.path.exists(PENDING_MQTT_FILE):
        return []
    try:
        with open(PENDING_MQTT_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Lỗi đọc pending_mqtt: %s", e)
        return []


def _save_pending(queue):
    try:
        tmp = PENDING_MQTT_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(queue, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, PENDING_MQTT_FILE)
    except Exception as e:
        logger.error("Lỗi ghi pending_mqtt: %s", e)


def _add_pending(record_serializable):
    """Lưu raw record (chưa build payload) vào pending."""
    queue = _load_pending()
    queue.append(record_serializable)
    _save_pending(queue)


def _remove_pending(record_serializable):
    queue = _load_pending()
    if record_serializable in queue:
        queue.remove(record_serializable)
        _save_pending(queue)


def count_pending():
    return len(_load_pending())


def _record_to_serializable(record):
    """Chuyển record (có datetime) thành dict JSON-safe để lưu file."""
    return {
        "timestamp": record["timestamp"].strftime("%Y-%m-%dT%H:%M:%S"),
        "values": record["values"],
    }


def _serializable_to_payload(item):
    """Build payload từ raw record lúc SẮP GỬI — dùng settings hiện tại."""
    from datetime import datetime
    s = settings_manager.load()
    values = item["values"]
    ts_str = item["timestamp"]

    def get_val(name):
        info = values.get(name, {})
        v = info.get("value")
        return round(v, 2) if v is not None else 0

    return {
        "ser_gw":     s["gateway_id"],
        "ser_dev":    "1",
        "time":       ts_str,
        "ph":         get_val("pH"),
        "tss":        get_val("TSS"),
        "temp":       get_val("Temp"),
        "nh4":        get_val("NH4+"),
        "flow_in":    get_val("Flow In"),
        "flow_out":   get_val("Flow Out"),
        "total_in":   get_val("Total In"),
        "total_out":  get_val("Total In_out"),
        "temp_iscan": get_val("Temp iScan"),
        "cod":        get_val("COD"),
    }


# _build_payload đã được thay bằng _serializable_to_payload (build lúc gửi, dùng settings hiện tại)


def _publish_one(payload):
    try:
        import paho.mqtt.client as mqtt
        s = settings_manager.load()

        client = mqtt.Client()

        if s["mqtt_user"]:
            client.username_pw_set(s["mqtt_user"], s["mqtt_pass"])

        # Timeout thật sự cho socket — tránh block mãi khi broker lag
        socket.setdefaulttimeout(CONNECT_TIMEOUT)
        try:
            client.connect(s["mqtt_host"], int(s["mqtt_port"]), keepalive=30)
        except Exception as e:
            logger.warning("MQTT connect thất bại: %s", e)
            return False
        finally:
            socket.setdefaulttimeout(None)  # Reset về mặc định

        client.loop_start()

        try:
            result = client.publish(
                s["mqtt_topic"],
                json.dumps(payload),
                qos=1
            )
            result.wait_for_publish(timeout=PUBLISH_TIMEOUT)

            if result.is_published():
                logger.info("MQTT publish thành công: gw=%s dev=%s time=%s topic=%s",
                            payload.get("ser_gw"),
                            payload.get("ser_dev"),
                            payload.get("time"),
                            s["mqtt_topic"])
                return True
            else:
                logger.warning("MQTT publish timeout: gw=%s dev=%s time=%s",
                               payload.get("ser_gw"),
                               payload.get("ser_dev"),
                               payload.get("time"))
                return False

        finally:
            client.loop_stop()
            client.disconnect()

    except Exception as e:
        logger.warning("MQTT publish thất bại: %s", e)
        return False


def publish_new(record):
    """Nhận record từ main, lưu raw vào pending, build payload lúc gửi."""
    item = _record_to_serializable(record)
    _add_pending(item)
    payload = _serializable_to_payload(item)
    if _publish_one(payload):
        _remove_pending(item)


def retry_pending():
    """Retry các record tồn đọng — build payload lúc gửi để dùng settings mới nhất."""
    queue = _load_pending()
    if not queue:
        return
    logger.info("MQTT retry %d record...", len(queue))
    for item in list(queue):
        payload = _serializable_to_payload(item)  # Build với settings hiện tại
        if _publish_one(payload):
            _remove_pending(item)
            # Delay 2-3 giây giữa mỗi record để không spam broker
            remaining = _load_pending()
            if remaining:
                delay = random.uniform(RETRY_DELAY_MIN, RETRY_DELAY_MAX)
                logger.debug("Chờ %.1fs trước khi gửi record tiếp theo...", delay)
                time.sleep(delay)
        else:
            # Publish thất bại → dừng retry, chờ lần sau
            break