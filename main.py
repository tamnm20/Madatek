# =============================================================================
# main.py — Vòng lặp chính của hệ thống
# Đọc Modbus liên tục để hiển thị LCD
# FTP và MQTT chạy trên thread riêng — main loop không bao giờ bị block
# =============================================================================

import time
import sys
import logging
import logging.handlers
import threading
import queue

import config
from modules import modbus_reader, file_writer, ftp_uploader, pending_queue, watchdog, settings_manager
from modules import mqtt_publisher
from modules.display import Dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.handlers.TimedRotatingFileHandler(
            "system.log",
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8"
        )
    ]
)
logger = logging.getLogger("main")


# =============================================================================
# FTP Worker — chạy trên thread riêng
# =============================================================================

class FTPWorker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._queue = queue.Queue()  # Queue nhận filepath mới cần upload

    def enqueue(self, filepath):
        """Gọi từ main thread để thêm file mới vào hàng chờ."""
        self._queue.put(filepath)

    def run(self):
        logger.info("FTP Worker started.")
        while True:
            try:
                # Chờ file mới tối đa 30 giây rồi retry pending
                try:
                    filepath = self._queue.get(timeout=30)
                    ftp_uploader.upload_new(filepath)
                except queue.Empty:
                    pass

                # Retry pending mỗi 30 giây
                ftp_uploader.retry_pending()

            except Exception as e:
                logger.error("FTP Worker lỗi: %s", e)
                time.sleep(5)


# =============================================================================
# MQTT Worker — chạy trên thread riêng
# =============================================================================

class MQTTWorker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._queue = queue.Queue()  # Queue nhận record mới cần publish

    def enqueue(self, record):
        """Gọi từ main thread để thêm record mới vào hàng chờ."""
        self._queue.put(record)

    def run(self):
        logger.info("MQTT Worker started.")
        while True:
            try:
                # Chờ record mới tối đa 30 giây rồi retry pending
                try:
                    record = self._queue.get(timeout=30)
                    mqtt_publisher.publish_new(record)
                except queue.Empty:
                    pass

                # Retry pending mỗi 30 giây
                mqtt_publisher.retry_pending()

            except Exception as e:
                logger.error("MQTT Worker lỗi: %s", e)
                time.sleep(5)


# =============================================================================
# Main
# =============================================================================

def main():
    logger.info("=== Hệ thống khởi động ===")
    logger.info("Demo mode: %s", config.DEMO_MODE)

    s = settings_manager.load()
    interval_display = s["interval_display"]
    interval_seconds = s["interval_seconds"]

    settings_changed = {"value": False}
    trigger_flag = {"value": False}

    def on_settings_saved():
        settings_changed["value"] = True
        settings_manager.reload()
        logger.info("Settings đã thay đổi, sẽ reload ở chu kỳ tiếp theo.")

    def on_trigger_data():
        """Callback từ nút Trigger Data: yêu cầu ghi + gửi ngay lập tức."""
        trigger_flag["value"] = True
        logger.info("Trigger Data được yêu cầu từ giao diện.")

    # Khởi động màn hình
    dashboard = Dashboard(
        on_settings_saved=on_settings_saved,
        on_trigger_data=on_trigger_data,
    )
    dashboard.start()
    time.sleep(1)

    # Khởi động FTP và MQTT worker trên thread riêng
    ftp_worker = FTPWorker()
    mqtt_worker = MQTTWorker()
    ftp_worker.start()
    mqtt_worker.start()

    last_display  = 0
    last_collect  = 0
    last_watchdog = 0
    last_record   = None

    logger.info("Hiển thị: %ds | Lưu file: %ds", interval_display, interval_seconds)

    while True:
        now = time.time()

        # --- Reload settings nếu người dùng vừa lưu ---
        if settings_changed["value"]:
            settings_changed["value"] = False
            s = settings_manager.load()
            interval_display = s["interval_display"]
            interval_seconds = s["interval_seconds"]
            logger.info("Đã reload settings. Hiển thị: %ds | Lưu file: %ds",
                        interval_display, interval_seconds)

        # --- Đọc Modbus liên tục + cập nhật màn hình ---
        if now - last_display >= interval_display:
            last_display = now
            record = modbus_reader.read_data()
            if record:
                last_record = record
                dashboard.update(record)

        # --- Trigger Data thủ công từ giao diện ---
        if trigger_flag["value"]:
            trigger_flag["value"] = False
            logger.info("--- Trigger Data thủ công ---")
            if last_record:
                filepath = file_writer.write_file(last_record)
                if filepath:
                    ftp_worker.enqueue(filepath)
                mqtt_worker.enqueue(last_record)
                logger.info("Trigger Data: đã ghi file và đẩy vào hàng chờ gửi.")
            else:
                logger.warning("Trigger Data: chưa có dữ liệu Modbus nào.")

        # --- Ghi file + đẩy vào FTP/MQTT worker mỗi N phút ---
        if now - last_collect >= interval_seconds:
            last_collect = now
            logger.info("--- Chu kỳ lưu file ---")
            if last_record:
                # 1. Ghi file
                filepath = file_writer.write_file(last_record)
                # 2. Đẩy vào FTP worker — không block main loop
                if filepath:
                    ftp_worker.enqueue(filepath)
                # 3. Đẩy vào MQTT worker — không block main loop
                mqtt_worker.enqueue(last_record)

            dashboard.update_pending(pending_queue.count())
            dashboard.update_mqtt_pending(mqtt_publisher.count_pending())

        # --- Cập nhật pending count lên màn hình mỗi 10 giây ---
        if now - last_collect >= 10:
            dashboard.update_pending(pending_queue.count())
            dashboard.update_mqtt_pending(mqtt_publisher.count_pending())

        # --- Watchdog ---
        if now - last_watchdog >= config.WATCHDOG_INTERVAL:
            last_watchdog = now
            watchdog.run_all()

        time.sleep(0.5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("=== Hệ thống dừng bởi người dùng ===")