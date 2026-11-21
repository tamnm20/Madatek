# =============================================================================
# modules/styles.py — Quản lý Bảng màu & Stylesheet (QSS) tập trung cho toàn bộ ứng dụng
# =============================================================================

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
        "input_disabled_bg": "#0a0a0a",
        "input_disabled_border": "#1a1a1a",
        "input_disabled_text": "#444444",
        "btn_save_disabled_bg": "#0a0a0a",
        "btn_save_disabled_text": "#333333",
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
        "input_disabled_bg": "#e2e8f0",
        "input_disabled_border": "#cbd5e1",
        "input_disabled_text": "#94a3b8",
        "btn_save_disabled_bg": "#e2e8f0",
        "btn_save_disabled_text": "#94a3b8",
    }
}


def _resolve_theme(theme):
    if isinstance(theme, str):
        return THEMES.get(theme, THEMES["dark"])
    return theme


def get_card_style(theme):
    """Style cho thẻ đo thông số (CardWidget)."""
    t = _resolve_theme(theme)
    return f"""
        QFrame {{
            background-color: {t['card_bg']};
            border: 1px solid {t['card_border']};
            border-radius: 6px;
        }}
    """


def get_nav_btn_style(theme):
    """Style cho các nút điều hướng Header (Home, Chart, Log, Settings)."""
    t = _resolve_theme(theme)
    return f"""
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


def get_theme_btn_style(theme):
    """Style cho nút chuyển Theme Sáng/Tối."""
    t = _resolve_theme(theme)
    return f"""
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
    """


def get_section_frame_style(theme):
    """Style cho các khung nhóm cấu hình (System, FTP, MQTT)."""
    t = _resolve_theme(theme)
    return f"""
        QFrame {{
            background-color: {t['card_bg']};
            border: 1px solid {t['card_border']};
            border-radius: 8px;
        }}
    """


def get_input_style(theme, enabled=True, is_password=False):
    """Style cho ô nhập liệu (QLineEdit)."""
    t = _resolve_theme(theme)
    border_radius = "6px 0px 0px 6px" if is_password else "6px"
    border_right = "border-right: none;" if is_password else ""

    if not enabled:
        bg = t.get("input_disabled_bg", "#0a0a0a")
        border = t.get("input_disabled_border", "#1a1a1a")
        color = t.get("input_disabled_text", "#444444")
        return f"""
            QLineEdit {{
                background-color: {bg};
                border: 1px solid {border};
                {border_right}
                border-radius: {border_radius};
                padding: 8px 12px;
                color: {color};
                font-size: 13px;
            }}
        """
    else:
        return f"""
            QLineEdit {{
                background-color: {t['chart_bg']};
                border: 1px solid {t['card_border']};
                {border_right}
                border-radius: {border_radius};
                padding: 8px 12px;
                color: {t['text']};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {t['accent']};
                {border_right}
            }}
        """


def get_pass_unlock_input_style(theme):
    """Style cho ô nhập mật khẩu mở khóa màn hình cài đặt."""
    t = _resolve_theme(theme)
    return f"""
        QLineEdit {{
            background-color: {t['chart_bg']};
            border: 1px solid {t['card_border']};
            border-radius: 6px;
            padding: 6px 10px;
            color: {t['text']};
            font-size: 13px;
        }}
        QLineEdit:focus {{ border: 1px solid {t['accent']}; }}
    """


def get_eye_btn_style(theme, enabled=True):
    """Style cho nút con mắt ẩn/hiện mật khẩu."""
    t = _resolve_theme(theme)
    if not enabled:
        bg = t.get("input_disabled_bg", "#0a0a0a")
        border = t.get("input_disabled_border", "#1a1a1a")
        color = t.get("input_disabled_text", "#444444")
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
    else:
        return f"""
            QPushButton {{
                background-color: {t['chart_bg']};
                border: 1px solid {t['card_border']};
                border-left: none;
                border-radius: 0px 6px 6px 0px;
                color: {t['label']};
                font-size: 14px;
            }}
            QPushButton:checked {{ color: {t['accent']}; }}
            QPushButton:hover {{ background-color: {t['card_border']}; }}
        """


def get_unlock_btn_style(theme):
    """Style cho nút Xác nhận mở khóa cài đặt."""
    t = _resolve_theme(theme)
    return f"""
        QPushButton {{
            background-color: {t['accent']};
            border: none;
            border-radius: 6px;
            color: {t['bg']};
            font-size: 12px;
            font-weight: bold;
        }}
        QPushButton:hover {{ opacity: 0.9; }}
    """


def get_close_btn_style(theme):
    """Style cho nút Đóng tab cài đặt."""
    t = _resolve_theme(theme)
    return f"""
        QPushButton {{
            background-color: transparent;
            border: 1px solid {t['status_warn']};
            border-radius: 6px;
            color: {t['status_warn']};
            font-size: 12px;
        }}
        QPushButton:hover {{ background-color: {t['card_bg']}; }}
    """


def get_cancel_btn_style():
    """Style cho nút Hủy thay đổi cài đặt."""
    return """
        QPushButton {
            background-color: transparent;
            border: 1px solid #444444;
            border-radius: 6px;
            color: #555555;
            font-size: 12px;
            font-weight: bold;
        }
        QPushButton:enabled {
            border: 2px solid #e05c5c;
            color: #e05c5c;
            background-color: transparent;
        }
        QPushButton:enabled:hover {
            background-color: #3a1010;
            border-color: #ff7070;
            color: #ff7070;
        }
        QPushButton:enabled:pressed {
            background-color: #5a1a1a;
        }
    """


def get_save_btn_style(theme):
    """Style cho nút Lưu cài đặt."""
    t = _resolve_theme(theme)
    disabled_bg = t.get("btn_save_disabled_bg", "#0a0a0a")
    disabled_text = t.get("btn_save_disabled_text", "#333333")
    return f"""
        QPushButton {{
            background-color: {disabled_bg};
            border: none;
            border-radius: 6px;
            color: {disabled_text};
            font-size: 12px;
            font-weight: bold;
        }}
        QPushButton:enabled {{
            background-color: {t['accent']};
            color: {t['bg']};
        }}
        QPushButton:enabled:hover {{ opacity: 0.9; }}
    """


def get_trigger_btn_style():
    """Style cho nút Trigger Data gửi ngay."""
    return """
        QPushButton {
            background-color: transparent;
            border: 2px solid #f59e0b;
            border-radius: 6px;
            color: #f59e0b;
            font-size: 12px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #2a1f00;
            border-color: #fbbf24;
            color: #fbbf24;
        }
        QPushButton:pressed {
            background-color: #3d2d00;
        }
    """


def get_shutdown_btn_style():
    """Style cho nút Tắt máy."""
    return """
        QPushButton {
            background-color: transparent;
            border: 2px solid #64748b;
            border-radius: 6px;
            color: #64748b;
            font-size: 12px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1a1f2a;
            border-color: #94a3b8;
            color: #94a3b8;
        }
        QPushButton:pressed {
            background-color: #0f1520;
            border-color: #475569;
            color: #475569;
        }
    """
