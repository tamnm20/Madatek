# =============================================================================
# config.py — Thông số CỐ ĐỊNH của hệ thống
# Thông số ĐỘNG (FTP, MQTT, Device ID, chu kỳ) → settings.json
# =============================================================================

# --- Chế độ chạy ---
DEMO_MODE = False               # TODO: False khi chạy thật

# --- Mật khẩu màn hình cài đặt ---
SETTINGS_PASSWORD = "1"  # TODO: đổi mật khẩu trước khi deploy

# --- Modbus TCP ---
MODBUS_HOST            = "192.168.25.1"   # TODO: IP thiết bị đối tác
MODBUS_PORT            = 502
MODBUS_UNIT_ID         = 1
MODBUS_BYTE_ORDER      = "big"           # "big" hoặc "little"
MODBUS_WORD_ORDER      = "big"           # "big" hoặc "little"
MODBUS_TIMEOUT         = 10

# Input Register (3xxxx) — FC4 — float32 (số thực)
MODBUS_INPUT_START     = 0               # 300001 → index 0
MODBUS_INPUT_COUNT     = 4               # 2 thông số × 2 register = 4
MODBUS_INPUT_DATA_TYPE = "float32"       # TODO: xác nhận Endian với đối tác

# Holding Register (4xxxx) — FC3 — int16
MODBUS_HOLDING_START     = 0             # 400001 → index 0
MODBUS_HOLDING_COUNT     = 8             # 400001 → 400008
MODBUS_HOLDING_DATA_TYPE = "int16"

# (index sau khi ghép, tên hiển thị, đơn vị, scale factor, min dummy, max dummy)
# float32: index 0-1 (không cần scale)
# int16:   index 2-9 (cần scale)
REGISTER_MAP = [
    (0, "pH",        "-",    1.0, 0.0,   14.0),    # 300001 → float[0]
    (1, "TSS",       "mg/L", 1.0, 0.0,   500.0),   # 300003 → float[1]
    (2, "Temp",      "°C",   0.1, 0.0,   50.0),    # 400001 → int[0]
    (3, "NH4+",      "mg/L", 0.1, 0.0,   200.0),   # 400002 → int[1]
    (4, "Flow In",   "m³/h", 0.1, 0.0,   50.0),    # 400003 → int[2]
    (5, "Flow Out",  "m³/h", 0.1, 0.0,   50.0),    # 400004 → int[3]
    (6, "Total In",  "m³",   0.1, 0.0,   99999.0), # 400005 → int[4]
    (8, "Temp iScan","°C",   0.1, 0.0,   50.0),    # 400007 → int[6]
    (9, "COD",       "mg/L", 0.1, 0.0,   500.0),   # 400008 → int[7]
]

# Total Out (400006 → int[5]) — gộp chung ô với Total In
REGISTER_PAIR = {
    "Total In": (7, "m³", 0.1, 0.0, 99999.0)
}

# --- Watchdog ---
WATCHDOG_INTERVAL   = 60   # Kiểm tra disk/RAM mỗi N giây
DISK_MIN_FREE_MB    = 500  # Cảnh báo nếu disk còn dưới N MB
MEMORY_WARN_PERCENT = 80   # Cảnh báo nếu RAM dùng trên N%

# --- Lưu file .txt ---
DATA_DIR      = "data"   # Thư mục lưu file
FILE_PREFIX   = "data"   # Tên file: data_YYYYMMDD_HHMMSS.txt
FILE_ENCODING = "utf-8"  # Encoding file

# --- Pending queue ---
PENDING_FILE = "pending.json"

# --- Giao diện LCD ---
DISPLAY_WIDTH     = 1024
DISPLAY_HEIGHT    = 600
DISPLAY_TITLE     = "Hệ thống quan trắc chất lượng nước và lưu lượng nước"
DISPLAY_HEADER    = "HỆ THỐNG QUAN TRẮC CHẤT LƯỢNG NƯỚC VÀ LƯU LƯỢNG NƯỚC"
DISPLAY_GRID_COLS = 3

# Màu sắc (mã hex)
COLOR_BG          = "#1a1a2e"  # Nền chính
COLOR_CARD_BG     = "#16213e"  # Nền card
COLOR_CARD_BORDER = "#0f3460"  # Viền card
COLOR_ACCENT      = "#4ade80"  # Màu số liệu
COLOR_TEXT        = "#ffffff"  # Chữ chính
COLOR_LABEL       = "#94a3b8"  # Chữ phụ
COLOR_STATUS_OK   = "#4ade80"  # Trạng thái bình thường
COLOR_STATUS_WARN = "#f59e0b"  # Trạng thái cảnh báo
COLOR_CHART_LINE  = "#4ade80"  # Đường biểu đồ
COLOR_CHART_BG    = "#0d1b2a"  # Nền biểu đồ

# Font chữ
FONT_NAME   = "Liberation Sans"
FONT_TITLE  = 10   # Cỡ chữ tên thông số
FONT_VALUE  = 20   # Cỡ chữ giá trị
FONT_UNIT   = 9    # Cỡ chữ đơn vị
FONT_STATUS = 8    # Cỡ chữ trạng thái
FONT_HEADER = 13   # Cỡ chữ tiêu đề

# Biểu đồ
CHART_MAX_POINTS = 60    # Số điểm lịch sử hiển thị
CHART_TICK_MS    = 500   # Tốc độ cập nhật UI (milliseconds)
CHART_FIG_WIDTH  = 2.8   # Chiều rộng biểu đồ mini
CHART_FIG_HEIGHT = 0.85  # Chiều cao biểu đồ mini
CHART_FIG_DPI    = 80    # Độ phân giải biểu đồ
CHART_LINE_WIDTH = 1.2   # Độ dày đường biểu đồ
CHART_FILL_ALPHA = 0.15  # Độ trong suốt phần fill