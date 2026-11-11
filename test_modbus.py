# =============================================================================
# test_modbus.py — Test kết nối Modbus TCP độc lập
# In ra kết quả giải mã theo tất cả tổ hợp Endian
# =============================================================================

import time
from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder

# ===== THAY ĐỔI CÁC THÔNG SỐ NÀY =====
HOST      = "192.168.25.1"
PORT      = 502
UNIT_ID   = 1
COUNT     = 20               # 10 nếu int16, 20 nếu float32, 40 nếu float64
START     = 0
REG_TYPE  = "input"          # "input" hoặc "holding"
DATA_TYPE = "float32"        # "int16" | "float32" | "float64"
TIMEOUT   = 10
DELAY     = 2
# =======================================

print(f"Đang kết nối {HOST}:{PORT} ...")
client = ModbusTcpClient(HOST, port=PORT, timeout=TIMEOUT)

if not client.connect():
    print("❌ Kết nối thất bại!")
    exit()

print(f"✅ Kết nối thành công! Chờ {DELAY}s...")
time.sleep(DELAY)

print(f"Đọc {COUNT} register từ địa chỉ {START} ({REG_TYPE} register), Unit ID={UNIT_ID} ...")

if REG_TYPE == "input":
    result = client.read_input_registers(address=START, count=COUNT, slave=UNIT_ID)
else:
    result = client.read_holding_registers(address=START, count=COUNT, slave=UNIT_ID)

client.close()

if result.isError():
    print(f"❌ Lỗi đọc register: {result}")
    exit()

# --- Raw registers ---
print(f"\n--- Raw registers ({len(result.registers)} giá trị) ---")
for i, val in enumerate(result.registers):
    print(f"  Register[{i+1}] = {val} (hex: {hex(val)})")

# --- Thử int16 × scale ---
if DATA_TYPE == "int16":
    print(f"\n--- Giải mã int16 × scale ---")
    for i, val in enumerate(result.registers):
        signed = val if val <= 32767 else val - 65536
        print(f"  Register[{i+1}] = {signed} | ×1={signed:.2f} | ×0.1={signed*0.1:.2f} | ×0.01={signed*0.01:.2f}")

# --- Thử float32 / float64 theo 4 tổ hợp Endian ---
if DATA_TYPE in ("float32", "float64"):
    endian_combos = [
        ("Big",    "Big",    ">", ">"),
        ("Big",    "Little", ">", "<"),
        ("Little", "Big",    "<", ">"),
        ("Little", "Little", "<", "<"),
    ]
    decode_fn_name      = "decode_32bit_float" if DATA_TYPE == "float32" else "decode_64bit_float"
    registers_per_value = 2 if DATA_TYPE == "float32" else 4

    for byte_label, word_label, byte_order, word_order in endian_combos:
        print(f"\n--- {DATA_TYPE} | Byte={byte_label} / Word={word_label} ---")
        try:
            decoder = BinaryPayloadDecoder.fromRegisters(
                result.registers,
                byteorder=byte_order,
                wordorder=word_order
            )
            decode_fn = getattr(decoder, decode_fn_name)
            for i in range(len(result.registers) // registers_per_value):
                val = decode_fn()
                print(f"  Thông số [{i+1}] = {val:.4f}")
        except Exception as e:
            print(f"  Lỗi: {e}")
