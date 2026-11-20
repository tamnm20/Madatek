# =============================================================================
# modules/settings_screen.py — Màn hình cài đặt (PyQt5)
# Mật khẩu nhập ngay trong màn hình, đúng thì enable input
# Nút Lưu/Hủy bên trái, bàn phím ảo tự hiện khi bấm vào ô input
# =============================================================================

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy, QAction
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from modules import settings_manager
from modules.keyboard import VirtualKeyboard
import config

logger = logging.getLogger(__name__)


class SettingsScreen(QWidget):
    def __init__(self, parent=None, on_settings_saved=None, on_close=None, on_trigger_data=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._settings = settings_manager.load()
        self._inputs = {}
        self._toggles = []
        self._section_frames = []
        self._section_titles = []
        self._field_labels = []
        self._unlocked = False
        self._toggle_action = None
        self._on_settings_saved = on_settings_saved
        self._on_close = on_close
        self._on_trigger_data = on_trigger_data
        self._keyboard = VirtualKeyboard(self)
        self._theme = {
            "bg": "#1a1a2e",
            "card_bg": "#16213e",
            "card_border": "#0f3460",
            "accent": "#4ade80",
            "text": "#ffffff",
            "label": "#94a3b8",
            "chart_bg": "#0d1b2a",
            "status_ok": "#4ade80",
            "status_warn": "#f59e0b",
        }
        self.setStyleSheet(f"background-color: {self._theme['bg']};")
        self._build_ui()

    def _font(self, size, bold=False):
        return QFont(config.FONT_NAME, size, QFont.Bold if bold else QFont.Normal)

    def _input_style_disabled(self):
        bg = self._theme.get('card_bg', '#0a0a0a')
        border = self._theme.get('card_border', '#1a1a1a')
        color = self._theme.get('label', '#444444')
        return f"""
            QLineEdit {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 8px 12px;
                color: {color};
                font-size: 13px;
            }}
        """

    def _input_style_enabled(self):
        return f"""
            QLineEdit {{
                background-color: {self._theme.get('chart_bg', '#0d1b2a')};
                border: 1px solid {self._theme.get('card_border', '#0f3460')};
                border-radius: 6px;
                padding: 8px 12px;
                color: {self._theme.get('text', '#ffffff')};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {self._theme.get('accent', '#4ade80')}; }}
        """

    def _input_pass_style_disabled(self):
        bg = self._theme.get('card_bg', '#0a0a0a')
        border = self._theme.get('card_border', '#1a1a1a')
        color = self._theme.get('label', '#444444')
        return f"""
            QLineEdit {{
                background-color: {bg};
                border: 1px solid {border};
                border-right: none;
                border-radius: 6px 0px 0px 6px;
                padding: 8px 12px;
                color: {color};
                font-size: 13px;
            }}
        """

    def _input_pass_style_enabled(self):
        return f"""
            QLineEdit {{
                background-color: {self._theme.get('chart_bg', '#0d1b2a')};
                border: 1px solid {self._theme.get('card_border', '#0f3460')};
                border-right: none;
                border-radius: 6px 0px 0px 6px;
                padding: 8px 12px;
                color: {self._theme.get('text', '#ffffff')};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {self._theme.get('accent', '#4ade80')}; border-right: none; }}
        """

    def _eye_style_disabled(self):
        bg = self._theme.get('card_bg', '#0a0a0a')
        border = self._theme.get('card_border', '#1a1a1a')
        color = self._theme.get('label', '#444444')
        return f"""
            QPushButton {{
                background-color: {bg};
                border: 1px solid {border};
                border-left: none;
                border-radius: 0px 6px 6px 0px;
                color: {color};
                font-size: 14px;
            }}
        """

    def _eye_style_enabled(self):
        return f"""
            QPushButton {{
                background-color: {self._theme.get('chart_bg', '#0d1b2a')};
                border: 1px solid {self._theme.get('card_border', '#0f3460')};
                border-left: none;
                border-radius: 0px 6px 6px 0px;
                color: {self._theme.get('label', '#94a3b8')};
                font-size: 14px;
            }}
            QPushButton:checked {{ color: {self._theme.get('accent', '#4ade80')}; }}
            QPushButton:hover {{ background-color: {self._theme.get('card_border', '#0f3460')}; }}
        """

    def _section_style(self):
        return f"""
            QFrame {{
                background-color: {self._theme.get('card_bg', '#16213e')};
                border: 1px solid {self._theme.get('card_border', '#0f3460')};
                border-radius: 8px;
            }}
        """

    def _connect_keyboard(self, inp):
        """Kết nối ô input với bàn phím ảo."""
        from PyQt5.QtWidgets import QLineEdit
        original_focus = inp.focusInEvent

        def on_focus(event, i=inp, orig=original_focus):
            orig(event)           # Gọi super để Qt xử lý focus/cursor đúng
            self._show_keyboard(i)

        inp.focusInEvent = on_focus

    def _show_keyboard(self, inp):
        """Hiện bàn phím ảo cho ô input được chọn."""
        if inp.isEnabled():
            self._keyboard.attach(inp)

    def mousePressEvent(self, event):
        """Bấm ra ngoài bàn phím → ẩn bàn phím."""
        if self._keyboard.isVisible():
            kb_rect = self._keyboard.geometry()
            if not kb_rect.contains(event.pos()):
                self._keyboard.detach()
        super().mousePressEvent(event)

    def _make_field(self, layout, label, key, password=False):
        lbl = QLabel(label)
        lbl.setFont(self._font(11))
        lbl.setStyleSheet(f"color: {self._theme.get('label', '#94a3b8')}; border: none;")
        self._field_labels.append(lbl)
        layout.addWidget(lbl)

        if password:
            row = QHBoxLayout()
            row.setSpacing(0)

            inp = QLineEdit()
            inp.setText(str(self._settings.get(key, "")))
            inp.setFixedHeight(42)
            inp.setEchoMode(QLineEdit.Password)
            inp.setEnabled(False)
            inp.setStyleSheet(self._input_pass_style_disabled())
            self._connect_keyboard(inp)

            btn_eye = QPushButton("🔒")
            btn_eye.setFixedSize(42, 42)
            btn_eye.setCheckable(True)
            btn_eye.setEnabled(False)
            btn_eye.setStyleSheet(self._eye_style_disabled())
            btn_eye.clicked.connect(lambda checked, i=inp, b=btn_eye: (
                i.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password),
                b.setText("🔓" if checked else "🔒")
            ))

            row.addWidget(inp)
            row.addWidget(btn_eye)
            layout.addLayout(row)

            self._inputs[key] = inp
            self._toggles.append((btn_eye, inp))
        else:
            inp = QLineEdit()
            inp.setText(str(self._settings.get(key, "")))
            inp.setFixedHeight(42)
            inp.setEnabled(False)
            inp.setStyleSheet(self._input_style_disabled())
            self._connect_keyboard(inp)
            layout.addWidget(inp)
            self._inputs[key] = inp

    def _make_section(self, title, fields):
        frame = QFrame()
        frame.setStyleSheet(self._section_style())
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._section_frames.append(frame)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setFont(self._font(12, bold=True))
        title_lbl.setStyleSheet(f"color: {self._theme.get('accent', '#4ade80')}; border: none;")
        self._section_titles.append(title_lbl)
        layout.addWidget(title_lbl)

        for field in fields:
            label, key = field[0], field[1]
            password = field[2] if len(field) > 2 else False
            self._make_field(layout, label, key, password=password)

        layout.addStretch()
        return frame

    def _toggle_pass_visibility(self):
        if self._pass_input.echoMode() == QLineEdit.Password:
            self._pass_input.setEchoMode(QLineEdit.Normal)
            self._toggle_action.setText("🔓")
        else:
            self._pass_input.setEchoMode(QLineEdit.Password)
            self._toggle_action.setText("🔒")

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 6, 16, 6)
        main_layout.setSpacing(6)

        # ── 1 hàng duy nhất: Cài đặt | Mật khẩu:[___] [Xác nhận] ✓ | [Hủy] [Lưu] | [✕Đóng] ──
        header = QHBoxLayout()
        header.setSpacing(8)

        # Tiêu đề
        self._title_lbl = QLabel("⚙  Cài đặt")
        self._title_lbl.setFont(self._font(13, bold=True))
        self._title_lbl.setStyleSheet(f"color: {config.COLOR_TEXT};")
        header.addWidget(self._title_lbl)

        header.addSpacing(16)

        # Mật khẩu
        self._pass_lbl = QLabel("Mật khẩu:")
        self._pass_lbl.setFont(self._font(11))
        self._pass_lbl.setStyleSheet(f"color: {config.COLOR_LABEL};")
        header.addWidget(self._pass_lbl)

        self._pass_input = QLineEdit()
        self._pass_input.setEchoMode(QLineEdit.Password)
        self._pass_input.setPlaceholderText("Mật khẩu...")
        self._pass_input.setFixedHeight(36)
        self._pass_input.setFixedWidth(140)
        self._pass_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {config.COLOR_CHART_BG};
                border: 1px solid {config.COLOR_CARD_BORDER};
                border-radius: 6px;
                padding: 6px 10px;
                color: {config.COLOR_TEXT};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {config.COLOR_ACCENT}; }}
        """)
        self._pass_input.returnPressed.connect(self._check_password)
        _orig_pass_focus = self._pass_input.focusInEvent
        def _pass_focus(event):
            _orig_pass_focus(event)
            self._keyboard.attach(self._pass_input)
        self._pass_input.focusInEvent = _pass_focus
        self._toggle_action = QAction("🔒", self._pass_input)
        self._toggle_action.triggered.connect(self._toggle_pass_visibility)
        self._pass_input.addAction(self._toggle_action, QLineEdit.TrailingPosition)
        header.addWidget(self._pass_input)

        self._btn_unlock = QPushButton("Xác nhận")
        self._btn_unlock.setFixedHeight(36)
        self._btn_unlock.setFixedWidth(90)
        self._btn_unlock.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_ACCENT};
                border: none;
                border-radius: 6px;
                color: {config.COLOR_BG};
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #36d46a; }}
        """)
        self._btn_unlock.clicked.connect(self._check_password)
        header.addWidget(self._btn_unlock)

        self._pass_status = QLabel("")
        self._pass_status.setFont(self._font(10))
        self._pass_status.setFixedWidth(100)
        self._pass_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.addWidget(self._pass_status)

        header.addStretch()

        # Nút Đóng
        self._btn_close = QPushButton("✕  Đóng")
        self._btn_close.setFixedHeight(36)
        self._btn_close.setFixedWidth(80)
        self._btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {config.COLOR_STATUS_WARN};
                border-radius: 6px;
                color: {config.COLOR_STATUS_WARN};
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {config.COLOR_CARD_BG}; }}
        """)
        self._btn_close.clicked.connect(self._close_view)
        header.addWidget(self._btn_close)

        main_layout.addLayout(header)

        # Hàng 2: Hủy | Lưu cài đặt | (stretch) | Trigger Data | Tắt máy
        action_row = QHBoxLayout()
        action_row.setSpacing(6)

        # --- Nút Hủy ---
        self._btn_cancel = QPushButton("✕  Hủy")
        self._btn_cancel.setFixedHeight(36)
        self._btn_cancel.setFixedWidth(100)
        self._btn_cancel.setEnabled(False)
        self._btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid #444444;
                border-radius: 6px;
                color: #555555;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:enabled {{
                border: 2px solid #e05c5c;
                color: #e05c5c;
                background-color: transparent;
            }}
            QPushButton:enabled:hover {{
                background-color: #3a1010;
                border-color: #ff7070;
                color: #ff7070;
            }}
            QPushButton:enabled:pressed {{
                background-color: #5a1a1a;
            }}
        """)
        self._btn_cancel.clicked.connect(self._close_view)

        # --- Nút Lưu cài đặt ---
        self._btn_save = QPushButton("✔  Lưu cài đặt")
        self._btn_save.setFixedHeight(36)
        self._btn_save.setFixedWidth(140)
        self._btn_save.setEnabled(False)
        self._btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: #0a0a0a;
                border: none;
                border-radius: 6px;
                color: #333333;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:enabled {{
                background-color: {config.COLOR_ACCENT};
                color: {config.COLOR_BG};
            }}
            QPushButton:enabled:hover {{ background-color: #36d46a; }}
            QPushButton:enabled:pressed {{ background-color: #28a857; }}
        """)
        self._btn_save.clicked.connect(self._save)

        # --- Nút Trigger Data ---
        self._btn_trigger = QPushButton("⚡  Trigger Data")
        self._btn_trigger.setFixedHeight(36)
        self._btn_trigger.setFixedWidth(150)
        self._btn_trigger.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid #f59e0b;
                border-radius: 6px;
                color: #f59e0b;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2a1f00;
                border-color: #fbbf24;
                color: #fbbf24;
            }}
            QPushButton:pressed {{
                background-color: #3d2d00;
            }}
        """)
        self._btn_trigger.clicked.connect(self._trigger_data)

        # --- Nút Tắt máy ---
        btn_shutdown = QPushButton("⏻  Tắt máy")
        btn_shutdown.setFixedHeight(36)
        btn_shutdown.setFixedWidth(120)
        btn_shutdown.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid #64748b;
                border-radius: 6px;
                color: #64748b;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #1a1f2a;
                border-color: #94a3b8;
                color: #94a3b8;
            }}
            QPushButton:pressed {{
                background-color: #0f1520;
                border-color: #475569;
                color: #475569;
            }}
        """)
        btn_shutdown.clicked.connect(self._shutdown)

        action_row.addSpacing(4)
        action_row.addWidget(self._btn_cancel)
        action_row.addSpacing(24)          # Khoảng cách Hủy ↔ Lưu rộng hơn
        action_row.addWidget(self._btn_save)
        action_row.addStretch()
        action_row.addWidget(self._btn_trigger)
        action_row.addSpacing(8)
        action_row.addWidget(btn_shutdown)
        action_row.addSpacing(4)
        main_layout.addLayout(action_row)

        # Divider
        self._divider = QFrame()
        self._divider.setFrameShape(QFrame.HLine)
        self._divider.setStyleSheet(f"color: {config.COLOR_CARD_BORDER};")
        main_layout.addWidget(self._divider)

        # 3 cột settings
        grid = QHBoxLayout()
        grid.setSpacing(10)

        col1 = QVBoxLayout()
        col1.addWidget(self._make_section("Thiết bị & Chu kỳ", [
            ("Gateway ID",            "gateway_id"),
            ("Device ID",             "device_id"),
            ("Lưu & gửi file (giây)", "interval_seconds"),
            ("Đọc Modbus (giây)",     "interval_display"),
        ]))

        col2 = QVBoxLayout()
        col2.addWidget(self._make_section("FTP Server", [
            ("Host / IP", "ftp_host"),
            ("Port",      "ftp_port"),
            ("Username",  "ftp_user"),
            ("Password",  "ftp_pass", True),
        ]))

        col3 = QVBoxLayout()
        col3.addWidget(self._make_section("MQTT Server", [
            ("Host / IP", "mqtt_host"),
            ("Port",      "mqtt_port"),
            ("Username",  "mqtt_user"),
            ("Password",  "mqtt_pass", True),
            ("Topic",     "mqtt_topic"),
        ]))

        grid.addLayout(col1)
        grid.addLayout(col2)
        grid.addLayout(col3)
        main_layout.addLayout(grid, stretch=1)

    def _check_password(self):
        self._keyboard.detach()
        if self._pass_input.text() == config.SETTINGS_PASSWORD:
            self._unlocked = True
            self._pass_input.setEnabled(False)
            self._pass_status.setText("✓ Đã mở khóa")
            self._pass_status.setStyleSheet(
                f"color: {self._theme.get('status_ok', '#4ade80')};")

            for key, inp in self._inputs.items():
                inp.setEnabled(True)
                if key in ("ftp_pass", "mqtt_pass"):
                    inp.setStyleSheet(self._input_pass_style_enabled())
                else:
                    inp.setStyleSheet(self._input_style_enabled())

            for btn_eye, inp in self._toggles:
                btn_eye.setEnabled(True)
                btn_eye.setStyleSheet(self._eye_style_enabled())

            self._btn_cancel.setEnabled(True)
            self._btn_save.setEnabled(True)

        else:
            self._pass_input.clear()
            self._pass_status.setText("✗ Sai mật khẩu!")
            self._pass_status.setStyleSheet("color: #e24b4a;")

    def _trigger_data(self):
        """Gọi callback Trigger Data về main.py, KHÔNG đóng tab."""
        self._keyboard.detach()
        logger.info("Trigger Data bấm từ màn hình cài đặt.")
        if self._on_trigger_data:
            self._on_trigger_data()

    def _shutdown(self):
        """Tắt Raspberry Pi."""
        import subprocess
        logger.info("Tắt máy được yêu cầu từ giao diện.")
        self._keyboard.detach()
        subprocess.Popen(["sudo", "shutdown", "-h", "now"])
        self._close_view()

    def _close_view(self):
        """Đóng/thoát tab cài đặt, quay về tab trước đó."""
        self._keyboard.detach()
        if self._on_close:
            self._on_close()

    def _save(self):
        if not self._unlocked:
            return
        self._keyboard.detach()
        for key, inp in self._inputs.items():
            val = inp.text().strip()
            if key in ("ftp_port", "mqtt_port",
                       "interval_seconds", "interval_display"):
                try:
                    val = int(val)
                except ValueError:
                    val = self._settings.get(key, 0)
            self._settings[key] = val

        if settings_manager.save(self._settings):
            logger.info("Settings đã lưu thành công")
            if self._on_settings_saved:
                self._on_settings_saved()
            self._close_view()
        else:
            logger.error("Lưu settings thất bại")

    def apply_theme(self, theme):
        """Cập nhật toàn bộ giao diện Cài đặt theo theme (Dark / Light)."""
        self._theme = theme
        self.setStyleSheet(f"background-color: {theme['bg']};")

        if hasattr(self, '_title_lbl'):
            self._title_lbl.setStyleSheet(f"color: {theme['text']};")
        if hasattr(self, '_pass_lbl'):
            self._pass_lbl.setStyleSheet(f"color: {theme['label']};")
        if hasattr(self, '_divider'):
            self._divider.setStyleSheet(f"color: {theme['card_border']};")

        if hasattr(self, '_pass_input'):
            self._pass_input.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {theme['chart_bg']};
                    border: 1px solid {theme['card_border']};
                    border-radius: 6px;
                    padding: 6px 10px;
                    color: {theme['text']};
                    font-size: 13px;
                }}
                QLineEdit:focus {{ border: 1px solid {theme['accent']}; }}
            """)

        if hasattr(self, '_btn_unlock'):
            self._btn_unlock.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme['accent']};
                    border: none;
                    border-radius: 6px;
                    color: {theme['bg']};
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ opacity: 0.9; }}
            """)

        if hasattr(self, '_btn_close'):
            self._btn_close.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {theme['card_border']};
                    border-radius: 6px;
                    color: {theme['label']};
                    font-size: 12px;
                }}
                QPushButton:hover {{ background-color: {theme['card_bg']}; }}
            """)

        for frame in self._section_frames:
            frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {theme['card_bg']};
                    border: 1px solid {theme['card_border']};
                    border-radius: 8px;
                }}
            """)

        for title in self._section_titles:
            title.setStyleSheet(f"color: {theme['accent']}; border: none;")

        for lbl in self._field_labels:
            lbl.setStyleSheet(f"color: {theme['label']}; border: none;")

        for key, inp in self._inputs.items():
            if self._unlocked:
                if key in ("ftp_pass", "mqtt_pass"):
                    inp.setStyleSheet(self._input_pass_style_enabled())
                else:
                    inp.setStyleSheet(self._input_style_enabled())
            else:
                if key in ("ftp_pass", "mqtt_pass"):
                    inp.setStyleSheet(self._input_pass_style_disabled())
                else:
                    inp.setStyleSheet(self._input_style_disabled())

        for btn_eye, _ in self._toggles:
            if self._unlocked:
                btn_eye.setStyleSheet(self._eye_style_enabled())
            else:
                btn_eye.setStyleSheet(self._eye_style_disabled())


def open_settings(parent=None, on_trigger_data=None):
    pass