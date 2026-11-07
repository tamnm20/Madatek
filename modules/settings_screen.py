# =============================================================================
# modules/settings_screen.py — Màn hình cài đặt (PyQt5)
# Mật khẩu nhập ngay trong màn hình, đúng thì enable input
# Nút Lưu/Hủy bên trái, bàn phím ảo tự hiện khi bấm vào ô input
# =============================================================================

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QSizePolicy, QAction
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from modules import settings_manager
from modules.keyboard import VirtualKeyboard
import config

logger = logging.getLogger(__name__)


class SettingsScreen(QDialog):
    def __init__(self, parent=None, on_trigger_data=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(config.DISPLAY_WIDTH, config.DISPLAY_HEIGHT)
        self.setStyleSheet(f"background-color: {config.COLOR_BG};")
        self._settings = settings_manager.load()
        self._inputs = {}
        self._toggles = []
        self._unlocked = False
        self._toggle_action = None
        self._on_trigger_data = on_trigger_data
        self._keyboard = VirtualKeyboard(self)
        self._build_ui()

    def _font(self, size, bold=False):
        return QFont(config.FONT_NAME, size, QFont.Bold if bold else QFont.Normal)

    def _input_style_disabled(self):
        return f"""
            QLineEdit {{
                background-color: #0a0a0a;
                border: 1px solid #1a1a1a;
                border-radius: 6px;
                padding: 8px 12px;
                color: #444444;
                font-size: 13px;
            }}
        """

    def _input_style_enabled(self):
        return f"""
            QLineEdit {{
                background-color: {config.COLOR_CHART_BG};
                border: 1px solid {config.COLOR_CARD_BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                color: {config.COLOR_TEXT};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {config.COLOR_ACCENT}; }}
        """

    def _input_pass_style_disabled(self):
        return f"""
            QLineEdit {{
                background-color: #0a0a0a;
                border: 1px solid #1a1a1a;
                border-right: none;
                border-radius: 6px 0px 0px 6px;
                padding: 8px 12px;
                color: #444444;
                font-size: 13px;
            }}
        """

    def _input_pass_style_enabled(self):
        return f"""
            QLineEdit {{
                background-color: {config.COLOR_CHART_BG};
                border: 1px solid {config.COLOR_CARD_BORDER};
                border-right: none;
                border-radius: 6px 0px 0px 6px;
                padding: 8px 12px;
                color: {config.COLOR_TEXT};
                font-size: 13px;
            }}
            QLineEdit:focus {{ border: 1px solid {config.COLOR_ACCENT}; border-right: none; }}
        """

    def _eye_style_disabled(self):
        return f"""
            QPushButton {{
                background-color: #0a0a0a;
                border: 1px solid #1a1a1a;
                border-left: none;
                border-radius: 0px 6px 6px 0px;
                color: #444444;
                font-size: 14px;
            }}
        """

    def _eye_style_enabled(self):
        return f"""
            QPushButton {{
                background-color: {config.COLOR_CHART_BG};
                border: 1px solid {config.COLOR_CARD_BORDER};
                border-left: none;
                border-radius: 0px 6px 6px 0px;
                color: {config.COLOR_LABEL};
                font-size: 14px;
            }}
            QPushButton:checked {{ color: {config.COLOR_ACCENT}; }}
            QPushButton:hover {{ background-color: {config.COLOR_CARD_BORDER}; }}
        """

    def _section_style(self):
        return f"""
            QFrame {{
                background-color: {config.COLOR_CARD_BG};
                border: 1px solid {config.COLOR_CARD_BORDER};
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
        lbl.setStyleSheet(f"color: {config.COLOR_LABEL}; border: none;")
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
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setFont(self._font(12, bold=True))
        title_lbl.setStyleSheet(f"color: {config.COLOR_ACCENT}; border: none;")
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
        title_lbl = QLabel("⚙  Cài đặt")
        title_lbl.setFont(self._font(13, bold=True))
        title_lbl.setStyleSheet(f"color: {config.COLOR_TEXT};")
        header.addWidget(title_lbl)

        header.addSpacing(16)

        # Mật khẩu
        pass_lbl = QLabel("Mật khẩu:")
        pass_lbl.setFont(self._font(11))
        pass_lbl.setStyleSheet(f"color: {config.COLOR_LABEL};")
        header.addWidget(pass_lbl)

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

        btn_unlock = QPushButton("Xác nhận")
        btn_unlock.setFixedHeight(36)
        btn_unlock.setFixedWidth(90)
        btn_unlock.setStyleSheet(f"""
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
        btn_unlock.clicked.connect(self._check_password)
        header.addWidget(btn_unlock)

        self._pass_status = QLabel("")
        self._pass_status.setFont(self._font(10))
        self._pass_status.setFixedWidth(100)
        self._pass_status.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.addWidget(self._pass_status)

        header.addStretch()

        # Nút Đóng
        btn_close = QPushButton("✕  Đóng")
        btn_close.setFixedHeight(36)
        btn_close.setFixedWidth(80)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {config.COLOR_STATUS_WARN};
                border-radius: 6px;
                color: {config.COLOR_STATUS_WARN};
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: {config.COLOR_CARD_BG}; }}
        """)
        btn_close.clicked.connect(self.reject)
        header.addWidget(btn_close)

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
        self._btn_cancel.clicked.connect(self.reject)

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
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {config.COLOR_CARD_BORDER};")
        main_layout.addWidget(line)

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
                f"color: {config.COLOR_STATUS_OK};")

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
        """Gọi callback Trigger Data về main.py, KHÔNG đóng dialog."""
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
        self.reject()

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
            self.accept()
        else:
            logger.error("Lưu settings thất bại")


def open_settings(parent=None, on_trigger_data=None):
    settings = SettingsScreen(parent, on_trigger_data=on_trigger_data)
    return settings.exec_() == QDialog.Accepted