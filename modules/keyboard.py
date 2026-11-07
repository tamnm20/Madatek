# =============================================================================
# modules/keyboard.py — Bàn phím ảo PyQt5
# Hiện khi bấm vào ô input, tắt khi bấm ra ngoài hoặc bấm Xong
# =============================================================================

from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QFont
import config


class VirtualKeyboard(QWidget):
    """Bàn phím ảo hiện phía dưới màn hình."""

    key_pressed = pyqtSignal(str)   # Phát signal khi bấm phím

    # Layout bàn phím — 2 chế độ: thường và Shift
    KEYS_NORMAL = [
        ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", ".", "-"],
        ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "@", "_"],
        ["a", "s", "d", "f", "g", "h", "j", "k", "l", ":", "/", "#"],
        ["z", "x", "c", "v", "b", "n", "m", "!", "SPACE", "⇧", "⌫"],
    ]

    KEYS_SHIFT = [
        ["!", "@", "#", "$", "%", "^", "&", "*", "(", ")", ",", "_"],
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "~", "+"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "?", "="],
        ["Z", "X", "C", "V", "B", "N", "M", "<", "SPACE", "⇧", "⌫"],
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shift = False
        self._target = None  # QLineEdit đang được focus
        self._build_ui()
        self.hide()

    def _btn_style(self, special=False):
        bg = config.COLOR_CARD_BORDER if special else config.COLOR_CARD_BG
        return f"""
            QPushButton {{
                background-color: {bg};
                border: 1px solid {config.COLOR_CARD_BORDER};
                border-radius: 4px;
                color: {config.COLOR_TEXT};
                font-size: 13px;
                font-weight: {'bold' if special else 'normal'};
            }}
            QPushButton:pressed {{
                background-color: {config.COLOR_ACCENT};
                color: {config.COLOR_BG};
            }}
        """

    def _build_ui(self):
        self.setStyleSheet(f"""
               QWidget {{
                   background-color: rgba(10, 10, 20, 220);
                   border-top: 2px solid {config.COLOR_CARD_BORDER};
               }}
           """)
        self._layout = QGridLayout(self)
        self._layout.setSpacing(3)
        self._layout.setContentsMargins(6, 6, 6, 6)
        self._buttons = {}
        self._render_keys()

    def _render_keys(self):
        # Xóa layout cũ
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._buttons.clear()

        keys = self.KEYS_SHIFT if self._shift else self.KEYS_NORMAL

        for row_idx, row in enumerate(keys):
            col_idx = 0
            for key in row:
                special = key in ("SPACE", "⌫", "⇧")

                btn = QPushButton()
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                btn.setFont(QFont(config.FONT_NAME, 12))

                if key == "SPACE":
                    btn.setText("SPACE")
                    btn.setStyleSheet(self._btn_style(special=True))
                    span = 2
                elif key == "⌫":
                    btn.setText("⌫")
                    btn.setStyleSheet(self._btn_style(special=True))
                    span = 1
                elif key == "⇧":
                    btn.setText("⇧ Shift")
                    btn.setStyleSheet(self._btn_style(special=self._shift))
                    if self._shift:
                        btn.setStyleSheet(f"""
                            QPushButton {{
                                background-color: {config.COLOR_ACCENT};
                                border: none;
                                border-radius: 4px;
                                color: {config.COLOR_BG};
                                font-size: 13px;
                                font-weight: bold;
                            }}
                        """)
                    span = 1
                else:
                    btn.setText(key)
                    btn.setStyleSheet(self._btn_style())
                    span = 1

                btn.clicked.connect(lambda _, k=key: self._on_key(k))
                self._layout.addWidget(btn, row_idx, col_idx, 1, span)
                col_idx += span

    def _on_key(self, key):
        if self._target is None:
            return

        if key == "⇧":
            self._shift = not self._shift
            self._render_keys()
            return
        elif key == "⌫":
            text = self._target.text()
            self._target.setText(text[:-1])
            return
        elif key == "SPACE":
            self._target.setText(self._target.text() + " ")
            return
        else:
            self._target.setText(self._target.text() + key)
            if self._shift:
                self._shift = False
                self._render_keys()

    def attach(self, line_edit, parent_height=None):
        """Gắn bàn phím vào ô input và hiện lên."""
        self._target = line_edit
        kb_height = 220
        # Dùng chiều cao thực tế của parent widget để tránh bị cắt
        if self.parent() is not None:
            actual_height = self.parent().height()
        else:
            actual_height = parent_height or config.DISPLAY_HEIGHT
        self.setFixedSize(config.DISPLAY_WIDTH, kb_height)
        self.move(0, actual_height - kb_height)
        self.raise_()
        self.show()

    def detach(self):
        """Ẩn bàn phím."""
        self._target = None
        self.hide()