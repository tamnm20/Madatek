# =============================================================================
# modules/file_writer.py — Ghi dữ liệu ra file .txt (atomic write)
# Mỗi 5 phút ghi 1 snapshot tại thời điểm đó, dạng bảng
# =============================================================================

import os
import logging
import config

logger = logging.getLogger(__name__)


def _ensure_dir():
    os.makedirs(config.DATA_DIR, exist_ok=True)


def _build_filename(timestamp):
    return os.path.join(
        config.DATA_DIR,
        f"{config.FILE_PREFIX}_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
    )


def _build_table(record):
    ts = record["timestamp"]
    values = record["values"]
    lines = []
    lines.append(f"Thời gian       : {ts.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("-" * 45)
    lines.append(f"{'Thông số':<12} {'Giá trị':>12} {'Đơn vị':<10}")
    lines.append("-" * 45)

    for _, name, unit, _, _, _ in config.REGISTER_MAP:
        info = values.get(name, {})
        val = info.get("value")
        unit_str = unit if unit else "-"
        if val is None:
            lines.append(f"{name:<12} {'---':>12} {unit_str:<10}")
        else:
            lines.append(f"{name:<12} {val:>12.2f} {unit_str:<10}")

    # Ghi REGISTER_PAIR (Total Out)
    for pair_name, (_, unit, _, _, _) in config.REGISTER_PAIR.items():
        out_key = pair_name + "_out"
        val = values.get(out_key, {}).get("value")
        unit_str = unit if unit else "-"
        label = pair_name + " Out"
        if val is None:
            lines.append(f"{label:<12} {'---':>12} {unit_str:<10}")
        else:
            lines.append(f"{label:<12} {val:>12.2f} {unit_str:<10}")

    lines.append("-" * 45)
    return "\n".join(lines) + "\n"


def write_file(record):
    """
    Ghi 1 snapshot ra file .txt theo kiểu atomic.
    Trả về đường dẫn file nếu thành công, None nếu lỗi.
    """
    try:
        _ensure_dir()
        filepath = _build_filename(record["timestamp"])
        tmp_path = filepath + ".tmp"
        content = _build_table(record)

        with open(tmp_path, "w", encoding=config.FILE_ENCODING) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, filepath)
        logger.info("Đã ghi file: %s", filepath)
        return filepath

    except Exception as e:
        logger.error("Lỗi ghi file: %s", e)
        return None
