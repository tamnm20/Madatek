# =============================================================================
# modules/modbus_reader.py — Đọc dữ liệu từ Modbus TCP
# Input Register  (3xxxx): FC4 — float32 — 300001, 300003
# Holding Register(4xxxx): FC3 — int16   — 400005 → 400012
# =============================================================================

import random
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)

_last_dummy = {}


def _read_dummy():
    global _last_dummy
    data = {}

    for _, name, unit, scale, lo, hi in config.REGISTER_MAP:
        mid = (lo + hi) / 2
        if name not in _last_dummy:
            _last_dummy[name] = mid
        step = (hi - lo) * 0.02
        new_val = _last_dummy[name] + random.uniform(-step, step)
        new_val = max(lo, min(hi, new_val))
        _last_dummy[name] = new_val
        data[name] = {"value": round(new_val, 2), "unit": unit}

    for pair_name, (_, unit, scale, lo, hi) in config.REGISTER_PAIR.items():
        out_key = pair_name + "_out"
        mid = (lo + hi) / 2
        if out_key not in _last_dummy:
            _last_dummy[out_key] = mid
        step = (hi - lo) * 0.02
        new_val = _last_dummy[out_key] + random.uniform(-step, step)
        new_val = max(lo, min(hi, new_val))
        _last_dummy[out_key] = new_val
        data[out_key] = {"value": round(new_val, 2), "unit": unit}

    return data


def _decode_float32(registers):
    """Giải mã float32 từ registers."""
    try:
        from pymodbus.payload import BinaryPayloadDecoder
        byte_order = ">" if config.MODBUS_BYTE_ORDER == "big" else "<"
        word_order = ">" if config.MODBUS_WORD_ORDER == "big" else "<"
        decoder = BinaryPayloadDecoder.fromRegisters(
            registers, byteorder=byte_order, wordorder=word_order)
        values = []
        for _ in range(len(registers) // 2):
            values.append(decoder.decode_32bit_float())
        return values
    except Exception as e:
        logger.error("Lỗi decode float32: %s", e)
        return None


def _decode_int16(registers):
    """Giải mã int16 từ registers."""
    values = []
    for reg in registers:
        v = reg & 0xFFFF
        if v > 32767:
            v -= 65536
        values.append(v)
    return values


def _read_modbus():
    try:
        from pymodbus.client import ModbusTcpClient
        client = ModbusTcpClient(
            config.MODBUS_HOST,
            port=config.MODBUS_PORT,
            timeout=config.MODBUS_TIMEOUT
        )
        if not client.connect():
            logger.error("Không thể kết nối Modbus: %s:%s",
                         config.MODBUS_HOST, config.MODBUS_PORT)
            return None

        # --- Đọc Input Register (3xxxx) — float32 ---
        input_result = client.read_input_registers(
            address=config.MODBUS_INPUT_START,
            count=config.MODBUS_INPUT_COUNT,
            slave=config.MODBUS_UNIT_ID
        )

        # --- Đọc Holding Register (4xxxx) — int16 ---
        holding_result = client.read_holding_registers(
            address=config.MODBUS_HOLDING_START,
            count=config.MODBUS_HOLDING_COUNT,
            slave=config.MODBUS_UNIT_ID
        )

        client.close()

        if input_result.isError():
            logger.error("Lỗi đọc Input Register: %s", input_result)
            return None

        if holding_result.isError():
            logger.error("Lỗi đọc Holding Register: %s", holding_result)
            return None

        # Decode riêng từng vùng
        input_values   = _decode_float32(list(input_result.registers))
        holding_values = _decode_int16(list(holding_result.registers))

        if input_values is None or holding_values is None:
            return None

        # Ghép lại: [float0, float1, int0, int1, int2, ...]
        # index 0 = pH (float), index 1 = TSS (float)
        # index 2+ = Temp, NH4+, Flow In... (int16)
        all_values = input_values + holding_values

        logger.info("Input float32: %s | Holding int16: %s",
                    [round(v, 3) for v in input_values],
                    holding_values)

        data = {}
        for i, (idx, name, unit, scale, _, _) in enumerate(config.REGISTER_MAP):
            # idx là vị trí trong all_values sau khi ghép
            if idx < len(all_values):
                raw = all_values[idx]
                # float32 không cần scale, int16 mới cần scale
                if idx < len(input_values):
                    data[name] = {"value": round(raw, 2), "unit": unit}
                else:
                    data[name] = {"value": round(raw * scale, 2), "unit": unit}
            else:
                data[name] = {"value": None, "unit": unit}

        if hasattr(config, 'REGISTER_PAIR'):
            for pair_name, (addr, unit, scale, _, _) in config.REGISTER_PAIR.items():
                out_key = pair_name + "_out"
                if addr < len(all_values):
                    raw = all_values[addr]
                    if addr < len(input_values):
                        data[out_key] = {"value": round(raw, 2), "unit": unit}
                    else:
                        data[out_key] = {"value": round(raw * scale, 2), "unit": unit}
                else:
                    data[out_key] = {"value": None, "unit": unit}

        return data

    except Exception as e:
        logger.error("Lỗi Modbus: %s", e)
        return None


def read_data():
    raw = _read_dummy() if config.DEMO_MODE else _read_modbus()
    if raw is None:
        return None
    return {"timestamp": datetime.now(), "values": raw}