# =============================================================================
# modules/display.py — Giao diện LCD 7 inch (PyQt5 + PyQtGraph)
# Dashboard dạng lưới tự động theo REGISTER_MAP và DISPLAY_GRID_COLS
# Thêm: nút Cài đặt, Device ID, MQTT status
# =============================================================================

import math
import threading
import logging
from collections import deque
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout,
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QPushButton
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import pyqtgraph as pg

import config
from modules import settings_manager

logger = logging.getLogger(__name__)


class CardWidget(QFrame):
    def __init__(self, name, unit, parent=None):
        super().__init__(parent)
        self.name = name
        self.unit = unit
        self.is_pair = name in config.REGISTER_PAIR
        self.history = deque([0.0] * config.CHART_MAX_POINTS,
                             maxlen=config.CHART_MAX_POINTS)
        self.has_data = False
        self.current_val = 0.0
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {config.COLOR_CARD_BG};
                border: 1px solid {config.COLOR_CARD_BORDER};
                border-radius: 6px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        top = QHBoxLayout()
        self.name_lbl = QLabel(self.name)
        self.name_lbl.setFont(QFont(config.FONT_NAME, config.FONT_TITLE, QFont.Bold))
        self.name_lbl.setStyleSheet(f"color: {config.COLOR_LABEL}; border: none;")

        self.status_lbl = QLabel("ĐANG ĐO")
        self.status_lbl.setFont(QFont(config.FONT_NAME, config.FONT_STATUS))
        self.status_lbl.setStyleSheet(f"color: {config.COLOR_STATUS_OK}; border: none;")
        self.status_lbl.setAlignment(Qt.AlignRight)

        top.addWidget(self.name_lbl)
        top.addWidget(self.status_lbl)
        layout.addLayout(top)

        mid = QHBoxLayout()
        self.value_lbl = QLabel("---")
        self.value_lbl.setFont(QFont(config.FONT_NAME, config.FONT_VALUE, QFont.Bold))
        self.value_lbl.setStyleSheet(f"color: {config.COLOR_ACCENT}; border: none;")

        if self.is_pair:
            pair_unit = config.REGISTER_PAIR[self.name][1]
            self.unit_lbl = QLabel(f"in {pair_unit}")
            self.unit_lbl.setFont(QFont(config.FONT_NAME, config.FONT_UNIT))
            self.unit_lbl.setStyleSheet(f"color: {config.COLOR_LABEL}; border: none;")
            self.unit_lbl.setAlignment(Qt.AlignBottom)
            mid.addWidget(self.value_lbl)
            mid.addWidget(self.unit_lbl)
            mid.addStretch()
            layout.addLayout(mid)

            mid2 = QHBoxLayout()
            self.value2_lbl = QLabel("---")
            self.value2_lbl.setFont(QFont(config.FONT_NAME, config.FONT_VALUE, QFont.Bold))
            self.value2_lbl.setStyleSheet(f"color: {config.COLOR_ACCENT}; border: none;")
            unit2_lbl = QLabel(f"out {pair_unit}")
            unit2_lbl.setFont(QFont(config.FONT_NAME, config.FONT_UNIT))
            unit2_lbl.setStyleSheet(f"color: {config.COLOR_LABEL}; border: none;")
            unit2_lbl.setAlignment(Qt.AlignBottom)
            mid2.addWidget(self.value2_lbl)
            mid2.addWidget(unit2_lbl)
            mid2.addStretch()
            layout.addLayout(mid2)
        else:
            self.unit_lbl = QLabel(self.unit if self.unit else "")
            self.unit_lbl.setFont(QFont(config.FONT_NAME, config.FONT_UNIT))
            self.unit_lbl.setStyleSheet(f"color: {config.COLOR_LABEL}; border: none;")
            self.unit_lbl.setAlignment(Qt.AlignBottom)
            mid.addWidget(self.value_lbl)
            mid.addWidget(self.unit_lbl)
            mid.addStretch()
            layout.addLayout(mid)

        pg.setConfigOptions(antialias=True)
        self.plot = pg.PlotWidget()
        self.plot.setBackground(config.COLOR_CHART_BG)
        self.plot.hideAxis("left")
        self.plot.hideAxis("bottom")
        self.plot.setMenuEnabled(False)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot.setMaximumHeight(60)

        pen = pg.mkPen(color=config.COLOR_CHART_LINE, width=config.CHART_LINE_WIDTH)
        self.curve = self.plot.plot(
            list(range(config.CHART_MAX_POINTS)),
            list(self.history),
            pen=pen
        )
        self.fill = pg.FillBetweenItem(
            self.curve,
            self.plot.plot([0, config.CHART_MAX_POINTS - 1], [0, 0]),
            brush=pg.mkBrush(color=(*self._hex_to_rgb(config.COLOR_CHART_LINE),
                                    int(255 * config.CHART_FILL_ALPHA)))
        )
        self.plot.addItem(self.fill)
        layout.addWidget(self.plot)

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def update_value(self, val, val2=None):
        if val is None:
            self.value_lbl.setText("---")
            return

        if not self.has_data:
            self.history = deque([val] * config.CHART_MAX_POINTS,
                                 maxlen=config.CHART_MAX_POINTS)
            self.current_val = val
            self.has_data = True
        else:
            self.current_val = val

        self.value_lbl.setText(f"{val:.2f}")

        if self.is_pair and val2 is not None:
            self.value2_lbl.setText(f"{val2:.2f}")

        self.history.append(self.current_val)
        ydata = list(self.history)
        self.curve.setData(list(range(config.CHART_MAX_POINTS)), ydata)

        ymin, ymax = min(ydata), max(ydata)
        margin = (ymax - ymin) * 0.15 if ymax != ymin else max(abs(ymin) * 0.1, 1)
        self.plot.setYRange(ymin - margin, ymax + margin, padding=0)


class MainWindow(QMainWindow):
    def __init__(self, on_settings_saved=None, on_trigger_data=None):
        super().__init__()
        self.on_settings_saved = on_settings_saved  # Callback khi lưu settings
        self.on_trigger_data = on_trigger_data       # Callback khi bấm Trigger Data
        self.setWindowTitle(config.DISPLAY_TITLE)
        self.setFixedSize(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT)
        self.setStyleSheet(f"background-color: {config.COLOR_BG};")

        self._cols = config.DISPLAY_GRID_COLS
        self._rows = math.ceil(len(config.REGISTER_MAP) / self._cols)
        self.cards = {}
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(4)

        # Header
        header = QHBoxLayout()

        title_lbl = QLabel(config.DISPLAY_HEADER)
        title_lbl.setFont(QFont(config.FONT_NAME, config.FONT_HEADER, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {config.COLOR_TEXT};")
        header.addWidget(title_lbl)

        header.addStretch()

        # Device ID
        s = settings_manager.load()
        self.device_lbl = QLabel(f"ID: {s.get('device_id', '---')}")
        self.device_lbl.setFont(QFont(config.FONT_NAME, config.FONT_STATUS))
        self.device_lbl.setStyleSheet(f"color: {config.COLOR_LABEL};")
        header.addWidget(self.device_lbl)

        # Thời gian
        self.time_lbl = QLabel("")
        self.time_lbl.setFont(QFont(config.FONT_NAME, config.FONT_STATUS))
        self.time_lbl.setStyleSheet(f"color: {config.COLOR_LABEL};")
        header.addWidget(self.time_lbl)

        # Nút Cài đặt
        self.btn_settings = QPushButton("⚙ Cài đặt")
        self.btn_settings.setFont(QFont(config.FONT_NAME, config.FONT_STATUS))
        self.btn_settings.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_CARD_BG};
                border: 1px solid {config.COLOR_ACCENT};
                border-radius: 4px;
                color: {config.COLOR_ACCENT};
                padding: 2px 10px;
            }}
            QPushButton:hover {{ background-color: {config.COLOR_CARD_BORDER}; }}
        """)
        self.btn_settings.clicked.connect(self._open_settings)
        header.addWidget(self.btn_settings)

        main_layout.addLayout(header)

        # Grid cards
        grid = QGridLayout()
        grid.setSpacing(6)
        for idx, (_, name, unit, _, _, _) in enumerate(config.REGISTER_MAP):
            row = idx // self._cols
            col = idx % self._cols
            card = CardWidget(name, unit)
            grid.addWidget(card, row, col)
            self.cards[name] = card
        main_layout.addLayout(grid)

        # Footer
        footer = QHBoxLayout()

        self.mqtt_lbl = QLabel("✓ MQTT OK")
        self.mqtt_lbl.setFont(QFont(config.FONT_NAME, config.FONT_STATUS))
        self.mqtt_lbl.setStyleSheet(f"color: {config.COLOR_STATUS_OK};")
        footer.addWidget(self.mqtt_lbl)

        footer.addStretch()

        self.pending_lbl = QLabel("✓ FTP OK")
        self.pending_lbl.setFont(QFont(config.FONT_NAME, config.FONT_STATUS))
        self.pending_lbl.setStyleSheet(f"color: {config.COLOR_STATUS_OK};")
        footer.addWidget(self.pending_lbl)

        main_layout.addLayout(footer)

    def _open_settings(self):
        """Mở màn hình cài đặt sau khi xác thực mật khẩu."""
        from modules.settings_screen import open_settings
        saved = open_settings(self, on_trigger_data=self.on_trigger_data)
        if saved:
            # Cập nhật Device ID trên header
            s = settings_manager.load()
            self.device_lbl.setText(f"ID: {s.get('device_id', '---')}")
            # Gọi callback để main.py reload settings
            if self.on_settings_saved:
                self.on_settings_saved()

    def refresh(self, latest, pending, mqtt_pending):
        for name, info in latest.items():
            if name in self.cards:
                val = info.get("value", 0)
                val2 = None
                if name in config.REGISTER_PAIR:
                    pair_name = name + "_out"
                    if pair_name in latest:
                        val2 = latest[pair_name].get("value", 0)
                self.cards[name].update_value(val, val2)

        self.time_lbl.setText(datetime.now().strftime("%d-%m-%Y  %H:%M:%S"))

        # FTP status
        if pending > 0:
            self.pending_lbl.setText(f"⚠ {pending} file FTP chờ")
            self.pending_lbl.setStyleSheet(f"color: {config.COLOR_STATUS_WARN};")
        else:
            self.pending_lbl.setText("✓ FTP OK")
            self.pending_lbl.setStyleSheet(f"color: {config.COLOR_STATUS_OK};")

        # MQTT status
        if mqtt_pending > 0:
            self.mqtt_lbl.setText(f"⚠ {mqtt_pending} MQTT chờ")
            self.mqtt_lbl.setStyleSheet(f"color: {config.COLOR_STATUS_WARN};")
        else:
            self.mqtt_lbl.setText("✓ MQTT OK")
            self.mqtt_lbl.setStyleSheet(f"color: {config.COLOR_STATUS_OK};")


class Dashboard:
    def __init__(self, on_settings_saved=None, on_trigger_data=None):
        self._latest = {}
        self._pending_count = 0
        self._mqtt_pending_count = 0
        self._lock = threading.Lock()
        self._app = None
        self._window = None
        self._on_settings_saved = on_settings_saved
        self._on_trigger_data = on_trigger_data

    def _run_ui(self):
        import sys
        self._app = QApplication.instance() or QApplication(sys.argv)
        self._window = MainWindow(
            on_settings_saved=self._on_settings_saved,
            on_trigger_data=self._on_trigger_data,
        )
        self._window.showFullScreen()

        timer = QTimer()
        timer.timeout.connect(self._on_tick)
        timer.start(config.CHART_TICK_MS)

        self._app.exec_()

    def _on_tick(self):
        with self._lock:
            latest       = dict(self._latest)
            pending      = self._pending_count
            mqtt_pending = self._mqtt_pending_count
        self._window.refresh(latest, pending, mqtt_pending)

    def update(self, record):
        with self._lock:
            self._latest = record.get("values", {})

    def update_pending(self, count):
        with self._lock:
            self._pending_count = count

    def update_mqtt_pending(self, count):
        with self._lock:
            self._mqtt_pending_count = count

    def start(self):
        t = threading.Thread(target=self._run_ui, daemon=True)
        t.start()
        logger.info("Display started.")