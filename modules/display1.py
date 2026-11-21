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
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QPushButton,
    QStackedWidget
)
from PyQt5.QtCore import Qt, QTimer, QSize, QPointF
from PyQt5.QtGui import (
    QFont, QIcon, QPixmap, QPainter, QPen, QColor, QBrush, QPainterPath
)
import pyqtgraph as pg

import config
from modules import settings_manager
from modules.settings_screen import SettingsScreen

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

        pg.setConfigOptions(antialias=False)
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

    def apply_theme(self, theme):
        """Cập nhật giao diện card theo theme (Sáng / Tối)."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme['card_bg']};
                border: 1px solid {theme['card_border']};
                border-radius: 6px;
            }}
        """)
        self.name_lbl.setStyleSheet(f"color: {theme['label']}; border: none;")
        self.value_lbl.setStyleSheet(f"color: {theme['accent']}; border: none;")
        self.unit_lbl.setStyleSheet(f"color: {theme['label']}; border: none;")
        self.status_lbl.setStyleSheet(f"color: {theme['status_ok']}; border: none;")
        if self.is_pair and hasattr(self, 'value2_lbl'):
            self.value2_lbl.setStyleSheet(f"color: {theme['accent']}; border: none;")

        # Cập nhật đồ thị PyQtGraph
        self.plot.setBackground(theme['chart_bg'])
        pen = pg.mkPen(color=theme['chart_line'], width=config.CHART_LINE_WIDTH)
        self.curve.setPen(pen)

        rgb = self._hex_to_rgb(theme['chart_line'])
        alpha = int(255 * theme.get('chart_fill_alpha', 0.15))
        self.fill.setBrush(pg.mkBrush(color=(*rgb, alpha)))

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


THEMES = {
    "dark": {
        "bg": "#1a1a2e",
        "card_bg": "#16213e",
        "card_border": "#0f3460",
        "accent": "#4ade80",
        "text": "#ffffff",
        "label": "#94a3b8",
        "status_ok": "#4ade80",
        "status_warn": "#f59e0b",
        "chart_bg": "#0d1b2a",
        "chart_line": "#4ade80",
        "chart_fill_alpha": 0.15,
    },
    "light": {
        "bg": "#f1f5f9",          # Xám sáng dịu chống chói (Slate 100)
        "card_bg": "#ffffff",     # Thẻ card trắng tinh
        "card_border": "#cbd5e1", # Viền card xám mảnh (Slate 300)
        "accent": "#059669",      # Xanh ngọc lục bảo đậm dễ đọc (Emerald 600)
        "text": "#0f172a",        # Chữ đen đậm rõ nét (Slate 900)
        "label": "#64748b",       # Chữ phụ xám trung tính (Slate 500)
        "status_ok": "#16a34a",   # Xanh lá cây tiêu chuẩn
        "status_warn": "#d97706", # Cam đậm
        "chart_bg": "#f8fafc",    # Nền biểu đồ sáng rất nhạt (Slate 50)
        "chart_line": "#059669",  # Đường line xanh đậm nét
        "chart_fill_alpha": 0.20,
    }
}


def create_nav_pixmap(icon_type, color_hex, size=24):
    """Vẽ icon vector độc lập với font hệ thống, bảo đảm luôn hiển thị sắc nét."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    color = QColor(color_hex)
    pen = QPen(color, 2)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)

    if icon_type == "home":
        # Mái nhà:
        path = QPainterPath()
        path.moveTo(3, 11)
        path.lineTo(12, 3.5)
        path.lineTo(21, 11)
        # Thân nhà & sàn:
        path.moveTo(6, 10.5)
        path.lineTo(6, 20.5)
        path.lineTo(18, 20.5)
        path.lineTo(18, 10.5)
        # Cửa nhà:
        path.moveTo(10, 20.5)
        path.lineTo(10, 15)
        path.lineTo(14, 15)
        path.lineTo(14, 20.5)
        painter.drawPath(path)

    elif icon_type == "chart":
        # Biểu đồ 3 cột:
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(4, 13, 3, 7, 1, 1)
        painter.drawRoundedRect(10, 5, 3, 15, 1, 1)
        painter.drawRoundedRect(16, 9, 3, 11, 1, 1)

    elif icon_type == "log":
        # Trang sổ / nhật ký:
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(5, 3, 14, 18, 2, 2)
        # 3 dòng ngang:
        path = QPainterPath()
        path.moveTo(8.5, 8)
        path.lineTo(15.5, 8)
        path.moveTo(8.5, 12)
        path.lineTo(15.5, 12)
        path.moveTo(8.5, 16)
        path.lineTo(13, 16)
        painter.drawPath(path)

    elif icon_type == "settings":
        # Bánh răng cài đặt:
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(12, 12), 4, 4)
        for i in range(6):
            angle = i * (math.pi / 3)
            x1 = 12 + 6 * math.cos(angle)
            y1 = 12 + 6 * math.sin(angle)
            x2 = 12 + 9.5 * math.cos(angle)
            y2 = 12 + 9.5 * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        painter.drawEllipse(QPointF(12, 12), 7, 7)

    elif icon_type == "sun":
        # Mặt trời: vòng tròn tâm + 8 tia sáng
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(12, 12), 4.5, 4.5)
        painter.setBrush(Qt.NoBrush)
        for i in range(8):
            angle = i * (math.pi / 4)
            x1 = 12 + 6.5 * math.cos(angle)
            y1 = 12 + 6.5 * math.sin(angle)
            x2 = 12 + 9.5 * math.cos(angle)
            y2 = 12 + 9.5 * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    elif icon_type == "moon":
            # Vẽ trăng lưỡi liềm quay lưng sang trái (chuẩn icon Dark Mode)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)

            outer_moon = QPainterPath()
            outer_moon.addEllipse(QPointF(12, 12), 8.5, 8.5)

            cutout = QPainterPath()  # Đảm bảo khởi tạo là QPainterPath
            cutout.addEllipse(QPointF(15.5, 9.5), 7.5, 7.5)  # Khoét lệch sang phải-trên

            crescent = outer_moon.subtracted(cutout)
            painter.drawPath(crescent)

    painter.end()
    return pixmap


def make_nav_icon(icon_type, theme=None):
    """Tạo QIcon có 2 trạng thái: bình thường và kích hoạt theo theme."""
    t = theme or THEMES["dark"]
    icon = QIcon()
    pix_off = create_nav_pixmap(icon_type, t["label"])
    icon.addPixmap(pix_off, QIcon.Normal, QIcon.Off)
    pix_on = create_nav_pixmap(icon_type, t["accent"])
    icon.addPixmap(pix_on, QIcon.Normal, QIcon.On)
    return icon


class MainWindow(QMainWindow):
    def __init__(self, on_settings_saved=None, on_trigger_data=None):
        super().__init__()
        self.on_settings_saved = on_settings_saved  # Callback khi lưu settings
        self.on_trigger_data = on_trigger_data       # Callback khi bấm Trigger Data
        self.current_theme = "dark"                  # Mặc định là Dark Mode
        self.setWindowTitle(config.DISPLAY_TITLE)
        self.setFixedSize(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT)
        self.setStyleSheet(f"background-color: {THEMES['dark']['bg']};")

        self._cols = config.DISPLAY_GRID_COLS
        self._rows = math.ceil(len(config.REGISTER_MAP) / self._cols)
        self.cards = {}
        self._build_ui()

    def _build_ui(self):
        t = THEMES[self.current_theme]
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(4)

        # =====================================================================
        # Header: [Madatek]  ---  [HỆ THỐNG QUAN TRẮC]  ---  [🏠] [📊] [📋] [☀️/🌙] [⚙]
        # =====================================================================
        header = QHBoxLayout()
        header.setContentsMargins(4, 2, 4, 2)
        header.setSpacing(8)

        # 1. Bên trái: Tên công ty Madatek
        self.company_lbl = QLabel("Madatek")
        self.company_lbl.setFont(QFont(config.FONT_NAME, 13, QFont.Bold))
        self.company_lbl.setStyleSheet(f"color: {t['accent']};")
        header.addWidget(self.company_lbl)

        header.addStretch(1)

        # 2. Ở giữa: Tiêu đề trang
        self.title_lbl = QLabel("HỆ THỐNG QUAN TRẮC")
        self.title_lbl.setFont(QFont(config.FONT_NAME, config.FONT_HEADER, QFont.Bold))
        self.title_lbl.setStyleSheet(f"color: {t['text']};")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        header.addWidget(self.title_lbl)

        header.addStretch(1)

        # 3. Cụm icon bên phải: Home, Biểu đồ, Log, Đổi Theme, Cài đặt
        nav_btn_style = f"""
            QPushButton {{
                background-color: {t['card_bg']};
                border: 1px solid {t['card_border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {t['card_border']};
                border-color: {t['accent']};
            }}
            QPushButton:checked {{
                background-color: {t['card_border']};
                border: 1px solid {t['accent']};
            }}
        """

        # 3.1. Nút Home (Trang chủ)
        self.btn_home = QPushButton()
        self.btn_home.setToolTip("Trang chủ")
        self.btn_home.setFixedSize(44, 36)
        self.btn_home.setIcon(make_nav_icon("home", t))
        self.btn_home.setIconSize(QSize(22, 22))
        self.btn_home.setCheckable(True)
        self.btn_home.setChecked(True)
        self.btn_home.setStyleSheet(nav_btn_style)
        self.btn_home.clicked.connect(lambda: self._switch_tab(0))
        header.addWidget(self.btn_home)

        # 3.2. Nút Biểu đồ
        self.btn_chart = QPushButton()
        self.btn_chart.setToolTip("Biểu đồ")
        self.btn_chart.setFixedSize(44, 36)
        self.btn_chart.setIcon(make_nav_icon("chart", t))
        self.btn_chart.setIconSize(QSize(22, 22))
        self.btn_chart.setCheckable(True)
        self.btn_chart.setStyleSheet(nav_btn_style)
        self.btn_chart.clicked.connect(lambda: self._switch_tab(1))
        header.addWidget(self.btn_chart)

        # 3.3. Nút Log
        self.btn_log = QPushButton()
        self.btn_log.setToolTip("Nhật ký / Log")
        self.btn_log.setFixedSize(44, 36)
        self.btn_log.setIcon(make_nav_icon("log", t))
        self.btn_log.setIconSize(QSize(22, 22))
        self.btn_log.setCheckable(True)
        self.btn_log.setStyleSheet(nav_btn_style)
        self.btn_log.clicked.connect(lambda: self._switch_tab(2))
        header.addWidget(self.btn_log)

        # 3.4. Nút Đổi Theme (Mặt trời: Dark->Light, Mặt trăng: Light->Dark)
        self.btn_theme = QPushButton()
        self.btn_theme.setFixedSize(44, 36)
        icon_theme = QIcon(create_nav_pixmap("sun", t["label"]))
        self.btn_theme.setIcon(icon_theme)
        self.btn_theme.setIconSize(QSize(22, 22))
        self.btn_theme.setToolTip("Chuyển sang giao diện Sáng")
        self.btn_theme.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['card_bg']};
                border: 1px solid {t['card_border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {t['card_border']};
                border-color: {t['accent']};
            }}
        """)
        self.btn_theme.clicked.connect(self._toggle_theme)
        header.addWidget(self.btn_theme)

        # 3.5. Nút Cài đặt (Tab 3)
        self.btn_settings = QPushButton()
        self.btn_settings.setToolTip("Cài đặt")
        self.btn_settings.setFixedSize(44, 36)
        self.btn_settings.setIcon(make_nav_icon("settings", t))
        self.btn_settings.setIconSize(QSize(22, 22))
        self.btn_settings.setCheckable(True)
        self.btn_settings.setStyleSheet(nav_btn_style)
        self.btn_settings.clicked.connect(lambda: self._switch_tab(3))
        header.addWidget(self.btn_settings)

        main_layout.addLayout(header)

        # =====================================================================
        # Khu vực nội dung: QStackedWidget hỗ trợ chuyển Tab
        # =====================================================================
        self.stack = QStackedWidget()

        # Tab 0: Home — Lưới các thẻ Card thông số
        page_home = QWidget()
        grid = QGridLayout(page_home)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(6)
        for idx, (_, name, unit, _, _, _) in enumerate(config.REGISTER_MAP):
            row = idx // self._cols
            col = idx % self._cols
            card = CardWidget(name, unit)
            grid.addWidget(card, row, col)
            self.cards[name] = card
        self.stack.addWidget(page_home)

        # Tab 1: Biểu đồ (Placeholder chờ phát triển)
        self.page_chart = QWidget()
        chart_layout = QVBoxLayout(self.page_chart)
        self.chart_lbl = QLabel("Tính năng Biểu đồ (Đang phát triển)")
        self.chart_lbl.setAlignment(Qt.AlignCenter)
        self.chart_lbl.setFont(QFont(config.FONT_NAME, 14, QFont.Bold))
        self.chart_lbl.setStyleSheet(f"color: {t['label']};")
        chart_layout.addWidget(self.chart_lbl)
        self.stack.addWidget(self.page_chart)

        # Tab 2: Log (Placeholder chờ phát triển)
        self.page_log = QWidget()
        log_layout = QVBoxLayout(self.page_log)
        self.log_lbl = QLabel("Tính năng Nhật ký / Log (Đang phát triển)")
        self.log_lbl.setAlignment(Qt.AlignCenter)
        self.log_lbl.setFont(QFont(config.FONT_NAME, 14, QFont.Bold))
        self.log_lbl.setStyleSheet(f"color: {t['label']};")
        log_layout.addWidget(self.log_lbl)
        self.stack.addWidget(self.page_log)

        # Tab 3: Cài đặt (Nhúng trực tiếp làm Tab, không popup)
        self.settings_page = SettingsScreen(
            parent=self,
            on_settings_saved=self._on_settings_saved_from_tab,
            on_close=lambda: self._switch_tab(0),
            on_trigger_data=self.on_trigger_data
        )
        self.stack.addWidget(self.settings_page)

        main_layout.addWidget(self.stack, stretch=1)

        # =====================================================================
        # Footer: [MQTT] [FTP] ... (stretch) ... [ID: xxx] [DD-MM-YYYY HH:MM:SS]
        # =====================================================================
        footer = QHBoxLayout()
        footer.setContentsMargins(4, 2, 4, 2)
        footer.setSpacing(14)

        # Trạng thái MQTT (bên trái 1)
        self.mqtt_lbl = QLabel("✓ MQTT OK")
        self.mqtt_lbl.setFont(QFont(config.FONT_NAME, config.FONT_STATUS))
        self.mqtt_lbl.setStyleSheet(f"color: {t['status_ok']};")
        footer.addWidget(self.mqtt_lbl)

        # Trạng thái FTP (bên trái 2)
        self.pending_lbl = QLabel("✓ FTP OK")
        self.pending_lbl.setFont(QFont(config.FONT_NAME, config.FONT_STATUS))
        self.pending_lbl.setStyleSheet(f"color: {t['status_ok']};")
        footer.addWidget(self.pending_lbl)

        footer.addStretch()

        # Device ID (bên phải 1)
        s = settings_manager.load()
        self.device_lbl = QLabel(f"ID: {s.get('device_id', '---')}")
        self.device_lbl.setFont(QFont(config.FONT_NAME, config.FONT_STATUS))
        self.device_lbl.setStyleSheet(f"color: {t['label']};")
        footer.addWidget(self.device_lbl)

        # Đồng hồ thời gian (bên phải 2)
        self.time_lbl = QLabel("")
        self.time_lbl.setFont(QFont(config.FONT_NAME, config.FONT_STATUS))
        self.time_lbl.setStyleSheet(f"color: {t['label']};")
        footer.addWidget(self.time_lbl)

        main_layout.addLayout(footer)

    def _toggle_theme(self):
        """Chuyển đổi qua lại giữa Dark Mode và Light Mode."""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme(new_theme)

    def apply_theme(self, theme_name):
        """Áp dụng toàn bộ màu sắc, icon, biểu đồ theo theme cho TẤT CẢ các tab."""
        self.current_theme = theme_name
        t = THEMES[theme_name]

        # 1. Nền cửa sổ chính
        self.setStyleSheet(f"background-color: {t['bg']};")

        # 2. Header text
        self.company_lbl.setStyleSheet(f"color: {t['accent']};")
        self.title_lbl.setStyleSheet(f"color: {t['text']};")

        # 3. Nav buttons
        nav_style = f"""
            QPushButton {{
                background-color: {t['card_bg']};
                border: 1px solid {t['card_border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {t['card_border']};
                border-color: {t['accent']};
            }}
            QPushButton:checked {{
                background-color: {t['card_border']};
                border: 1px solid {t['accent']};
            }}
        """
        for btn in (self.btn_home, self.btn_chart, self.btn_log, self.btn_settings):
            btn.setStyleSheet(nav_style)

        self.btn_home.setIcon(make_nav_icon("home", t))
        self.btn_chart.setIcon(make_nav_icon("chart", t))
        self.btn_log.setIcon(make_nav_icon("log", t))
        self.btn_settings.setIcon(make_nav_icon("settings", t))

        # 4. Nút Theme (cập nhật icon và tooltip)
        if theme_name == "dark":
            self.btn_theme.setIcon(QIcon(create_nav_pixmap("sun", t["label"])))
            self.btn_theme.setToolTip("Chuyển sang giao diện Sáng")
        else:
            self.btn_theme.setIcon(QIcon(create_nav_pixmap("moon", t["label"])))
            self.btn_theme.setToolTip("Chuyển sang giao diện Tối")

        self.btn_theme.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['card_bg']};
                border: 1px solid {t['card_border']};
                border-radius: 6px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {t['card_border']};
                border-color: {t['accent']};
            }}
        """)

        # 5. Toàn bộ các thẻ Card (Tab 0)
        for card in self.cards.values():
            card.apply_theme(t)

        # 6. Tab 1 (Biểu đồ)
        if hasattr(self, 'page_chart'):
            self.page_chart.setStyleSheet(f"background-color: {t['bg']};")
        if hasattr(self, 'chart_lbl'):
            self.chart_lbl.setStyleSheet(f"color: {t['label']};")

        # 7. Tab 2 (Log)
        if hasattr(self, 'page_log'):
            self.page_log.setStyleSheet(f"background-color: {t['bg']};")
        if hasattr(self, 'log_lbl'):
            self.log_lbl.setStyleSheet(f"color: {t['label']};")

        # 8. Tab 3 (Cài đặt)
        if hasattr(self, 'settings_page'):
            self.settings_page.apply_theme(t)

        # 9. Footer
        self.device_lbl.setStyleSheet(f"color: {t['label']};")
        self.time_lbl.setStyleSheet(f"color: {t['label']};")

    def _switch_tab(self, index):
        """Chuyển đổi giữa các tab trên giao diện chính."""
        self.stack.setCurrentIndex(index)
        self.btn_home.setChecked(index == 0)
        self.btn_chart.setChecked(index == 1)
        self.btn_log.setChecked(index == 2)
        self.btn_settings.setChecked(index == 3)

    def _on_settings_saved_from_tab(self):
        """Callback khi lưu settings từ tab Cài đặt."""
        s = settings_manager.load()
        self.device_lbl.setText(f"ID: {s.get('device_id', '---')}")
        if self.on_settings_saved:
            self.on_settings_saved()

    def refresh(self, latest, pending, mqtt_pending, is_new_data=True):
        t = THEMES[self.current_theme]
        # Chỉ cập nhật thẻ Card và vẽ lại biểu đồ khi có dữ liệu Modbus mới
        if is_new_data and latest:
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
            self.pending_lbl.setStyleSheet(f"color: {t['status_warn']};")
        else:
            self.pending_lbl.setText("✓ FTP OK")
            self.pending_lbl.setStyleSheet(f"color: {t['status_ok']};")

        # MQTT status
        if mqtt_pending > 0:
            self.mqtt_lbl.setText(f"⚠ {mqtt_pending} MQTT chờ")
            self.mqtt_lbl.setStyleSheet(f"color: {t['status_warn']};")
        else:
            self.mqtt_lbl.setText("✓ MQTT OK")
            self.mqtt_lbl.setStyleSheet(f"color: {t['status_ok']};")


class Dashboard:
    def __init__(self, on_settings_saved=None, on_trigger_data=None):
        self._latest = {}
        self._pending_count = 0
        self._mqtt_pending_count = 0
        self._data_version = 0          # Tăng mỗi khi có dữ liệu Modbus mới
        self._last_rendered_ver = -1     # Theo dõi version đã vẽ biểu đồ
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
            data_ver     = self._data_version

        is_new_data = (data_ver != self._last_rendered_ver)
        if is_new_data:
            self._last_rendered_ver = data_ver

        self._window.refresh(latest, pending, mqtt_pending, is_new_data=is_new_data)

    def update(self, record):
        with self._lock:
            self._latest = record.get("values", {})
            self._data_version += 1

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