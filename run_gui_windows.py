# =============================================================================
# run_gui_windows.py — Chạy thử & Xem trước Giao diện trực tiếp trên Windows
# Không cần Raspberry Pi, không cần Modbus/MQTT/FTP thật.
#
# Cách chạy:
#   1. Cài thư viện (chỉ cần chạy 1 lần):
#      pip install PyQt5 pyqtgraph
#   2. Khởi chạy:
#      python run_gui_windows.py
# =============================================================================

import sys
import random
import os
from datetime import datetime

# Đảm bảo import được các module từ thư mục gốc
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    import pyqtgraph as pg
except ImportError:
    print("\n" + "=" * 60)
    print(" LỖI: Chưa cài đặt thư viện PyQt5 hoặc pyqtgraph trên Windows!")
    print(" Vui lòng chạy lệnh sau trong Terminal / Command Prompt:")
    print("\n    pip install PyQt5 pyqtgraph\n")
    print("=" * 60 + "\n")
    sys.exit(1)

import config
from modules.display import MainWindow, THEMES


class WindowsSimulator:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle("Fusion")

        # Khởi tạo cửa sổ chính
        self.window = MainWindow(
            on_settings_saved=self._on_settings_saved,
            on_trigger_data=self._on_trigger_data,
        )

        # Chế độ cửa sổ trên Windows (thay vì Fullscreen như trên Pi)
        # Kích thước đúng chuẩn màn hình LCD 7 inch (1024x600)
        self.window.resize(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT)
        self.window.setWindowTitle(f"{config.DISPLAY_TITLE} — [WINDOWS PREVIEW]")
        self.window.show()

        # Dữ liệu giả lập ban đầu
        self.sim_values = {}
        for _, name, unit, scale, min_v, max_v in config.REGISTER_MAP:
            mid = (min_v + max_v) / 2
            self.sim_values[name] = mid

        for name in config.REGISTER_PAIR:
            self.sim_values[name + "_out"] = 100.0

        # Timer tạo dữ liệu giả lập mỗi 1 giây (như Modbus thật)
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self._generate_random_data)
        self.sim_timer.start(1000)

        # Timer cập nhật giao diện mỗi 500ms
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self._tick_ui)
        self.ui_timer.start(config.CHART_TICK_MS)

        self._has_new_data = True
        self._pending_files = 0
        self._pending_mqtt = 0

    def _on_settings_saved(self):
        print("[PREVIEW] Đã lưu cài đặt mới từ Tab Cài đặt!")

    def _on_trigger_data(self):
        print("[PREVIEW] Đã bấm nút 'Gửi dữ liệu ngay (Trigger)'!")

    def _generate_random_data(self):
        """Giả lập biến động thông số cảm biến Modbus ngẫu nhiên."""
        for _, name, unit, scale, min_v, max_v in config.REGISTER_MAP:
            delta = (max_v - min_v) * 0.03 * (random.random() - 0.5)
            new_val = max(min_v, min(max_v, self.sim_values[name] + delta))
            self.sim_values[name] = round(new_val, 2)

        for name in config.REGISTER_PAIR:
            pair_key = name + "_out"
            self.sim_values[pair_key] = round(self.sim_values.get(pair_key, 100.0) + (random.random() - 0.5) * 5, 2)

        self._has_new_data = True

    def _tick_ui(self):
        """Cập nhật giao diện preview."""
        # Chuyển đổi dữ liệu sang định dạng mà MainWindow.refresh nhận
        latest_record = {
            name: {"value": val} for name, val in self.sim_values.items()
        }

        # Gọi refresh với cờ is_new_data
        self.window.refresh(
            latest=latest_record,
            pending=self._pending_files,
            mqtt_pending=self._pending_mqtt,
            is_new_data=self._has_new_data
        )
        self._has_new_data = False

    def run(self):
        print("\n" + "=" * 60)
        print(" Đang chạy Giao diện xem trước trên Windows (1024x600)...")
        print(" - Bấm 🏠 / 📊 / 📋 / ⚙ để chuyển các tab.")
        print(" - Bấm ☀️ / 🌙 để chuyển đổi chế độ Sáng / Tối.")
        print(f" - Mật khẩu tab Cài đặt: {config.SETTINGS_PASSWORD}")
        print(" - Tắt cửa sổ để kết thúc.")
        print("=" * 60 + "\n")
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    sim = WindowsSimulator()
    sim.run()
