# =============================================================================
# test_headless.py — Kiểm tra toàn bộ logic KHÔNG cần GUI (PyQt5/display)
# Dùng để test trên GitHub Codespaces / Google Cloud Shell / server headless
#
# CÁCH CHẠY:
#   python test_headless.py              # Test cơ bản (không cần MQTT/FTP thật)
#   python test_headless.py --ftp        # Test FTP (tự khởi động server demo nội bộ)
#   python test_headless.py --mqtt       # Test MQTT thật (cần broker online)
#   python test_headless.py --all        # Chạy tất cả
#
# SETUP TRÊN GITHUB CODESPACES / CLOUD SHELL:
#   git clone <repo>
#   cd boxdata
#   pip install pymodbus paho-mqtt psutil pyftpdlib
#   python test_headless.py --all
#
# MODULES ĐƯỢC TEST (không cần display):
#   [1] settings_manager  — Đọc/ghi settings.json
#   [2] modbus_reader     — Demo mode (random data)
#   [3] file_writer       — Ghi file .txt (atomic write)
#   [4] pending_queue     — Hàng chờ FTP (persistent JSON)
#   [5] ftp_uploader      — Upload FTP (--ftp)
#   [6] mqtt_publisher    — Publish MQTT (--mqtt)
#   [7] watchdog          — Giám sát disk/RAM
#   [8] integration loop  — 5 chu kỳ đọc-ghi-queue
#   [9] mqtt payload      — Kiểm tra JSON payload (không gửi thật)
#  [10] dependencies      — Kiểm tra thư viện đã cài
# =============================================================================

import sys
import os
import time
import json
import shutil
import threading
import argparse
import traceback
from datetime import datetime

# Fix encoding cho Windows terminal
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Màu ANSI — tự tắt nếu terminal không hỗ trợ
# ---------------------------------------------------------------------------
USE_COLOR = sys.stdout.isatty() or os.environ.get("FORCE_COLOR")

def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text

def GREEN(t):  return _c("92", t)
def RED(t):    return _c("91", t)
def YELLOW(t): return _c("93", t)
def CYAN(t):   return _c("96", t)
def BOLD(t):   return _c("1",  t)
def DIM(t):    return _c("2",  t)

# ---------------------------------------------------------------------------
# Kết quả test
# ---------------------------------------------------------------------------
_results = []   # list of (name, passed, message)

def _ok(name, msg=""):
    _results.append((name, True, msg))
    print(f"  {GREEN('✔')} {name}" + (f" — {DIM(msg)}" if msg else ""))

def _fail(name, msg=""):
    _results.append((name, False, msg))
    print(f"  {RED('✘')} {name}" + (f" — {RED(msg)}" if msg else ""))

def _skip(name, msg=""):
    _results.append((name, None, msg))
    print(f"  {YELLOW('–')} {name} {DIM('(bỏ qua)')}" + (f" — {DIM(msg)}" if msg else ""))

def section(title):
    print(f"\n{BOLD(CYAN('═══ ' + title + ' ═══'))}")

# ---------------------------------------------------------------------------
# Patch: ngăn PyQt5 / tkinter bị import (phòng môi trường headless)
# ---------------------------------------------------------------------------
import unittest.mock as mock
sys.modules.setdefault("PyQt5",                    mock.MagicMock())
sys.modules.setdefault("PyQt5.QtWidgets",          mock.MagicMock())
sys.modules.setdefault("PyQt5.QtCore",             mock.MagicMock())
sys.modules.setdefault("PyQt5.QtGui",              mock.MagicMock())
sys.modules.setdefault("pyqtgraph",                mock.MagicMock())

# ---------------------------------------------------------------------------
# Đảm bảo cwd = thư mục chứa main.py
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)


# =============================================================================
# 1. SETTINGS MANAGER
# =============================================================================
def test_settings():
    section("1. Settings Manager")
    try:
        from modules import settings_manager

        # Reset cache để đọc tươi
        settings_manager._cache = None
        s = settings_manager.load()

        required_keys = [
            "gateway_id", "device_id",
            "ftp_host", "ftp_port", "ftp_user", "ftp_pass",
            "mqtt_host", "mqtt_port", "mqtt_user", "mqtt_pass", "mqtt_topic",
            "interval_seconds", "interval_display",
        ]
        missing = [k for k in required_keys if k not in s]
        if missing:
            _fail("load() — đủ keys", f"thiếu: {missing}")
        else:
            _ok("load() — đủ keys", f"{len(required_keys)} keys OK")

        # Test save + reload
        backup = dict(s)
        s["_test_key"] = "hello"
        ok = settings_manager.save(s)
        if not ok:
            _fail("save() — ghi file")
        else:
            _ok("save() — ghi file")

        settings_manager._cache = None
        s2 = settings_manager.load()
        if s2.get("_test_key") == "hello":
            _ok("reload() — đọc lại đúng")
        else:
            _fail("reload() — đọc lại đúng")

        # Khôi phục
        if "_test_key" in backup:
            del backup["_test_key"]
        settings_manager.save(backup)
        settings_manager._cache = None

    except Exception as e:
        _fail("settings_manager — exception", str(e))
        traceback.print_exc()


# =============================================================================
# 2. MODBUS READER (demo mode)
# =============================================================================
def test_modbus_reader():
    section("2. Modbus Reader (Demo Mode)")
    try:
        import config
        original = config.DEMO_MODE
        config.DEMO_MODE = True

        from modules import modbus_reader
        modbus_reader._last_dummy = {}

        record = modbus_reader.read_data()
        if record is None:
            _fail("read_data() — trả về dữ liệu")
            return

        _ok("read_data() — không None")

        # Kiểm tra cấu trúc
        if "timestamp" not in record:
            _fail("record có key 'timestamp'")
        else:
            _ok("record có key 'timestamp'", str(record["timestamp"])[:19])

        if "values" not in record:
            _fail("record có key 'values'")
        else:
            vals = record["values"]
            _ok("record có key 'values'", f"{len(vals)} thông số")

            # Kiểm tra từng thông số
            expected_names = [name for (_, name, _, _, _, _) in config.REGISTER_MAP]
            for name in expected_names:
                if name not in vals:
                    _fail(f"  thông số '{name}'", "thiếu")
                else:
                    v = vals[name].get("value")
                    u = vals[name].get("unit", "")
                    _ok(f"  {name}", f"{v} {u}")

        config.DEMO_MODE = original

    except Exception as e:
        _fail("modbus_reader — exception", str(e))
        traceback.print_exc()


# =============================================================================
# 3. FILE WRITER
# =============================================================================
def test_file_writer():
    section("3. File Writer")
    try:
        import config
        original_demo = config.DEMO_MODE
        config.DEMO_MODE = True

        from modules import modbus_reader, file_writer
        modbus_reader._last_dummy = {}

        record = modbus_reader.read_data()
        if record is None:
            _fail("cần dữ liệu từ modbus_reader")
            return

        filepath = file_writer.write_file(record)
        if filepath is None:
            _fail("write_file() — tạo file")
            return
        _ok("write_file() — tạo file", os.path.basename(filepath))

        if os.path.exists(filepath):
            _ok("file tồn tại trên disk", filepath)
        else:
            _fail("file tồn tại trên disk")
            return

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if "Thời gian" in content:
            _ok("nội dung có 'Thời gian'")
        else:
            _fail("nội dung có 'Thời gian'")

        expected_names = [name for (_, name, _, _, _, _) in config.REGISTER_MAP]
        for name in expected_names:
            if name in content:
                _ok(f"  nội dung có '{name}'")
            else:
                _fail(f"  nội dung có '{name}'", "THIẾU")

        # Lưu lại filepath để test FTP dùng
        test_file_writer._last_filepath = filepath
        config.DEMO_MODE = original_demo

    except Exception as e:
        _fail("file_writer — exception", str(e))
        traceback.print_exc()

test_file_writer._last_filepath = None


# =============================================================================
# 4. PENDING QUEUE (FTP)
# =============================================================================
def test_pending_queue():
    section("4. Pending Queue (FTP)")
    try:
        from modules import pending_queue
        import config

        # Backup file gốc
        backup_file = config.PENDING_FILE + ".bak"
        if os.path.exists(config.PENDING_FILE):
            shutil.copy2(config.PENDING_FILE, backup_file)

        # Dùng file tạm để không ảnh hưởng production
        orig_pending = config.PENDING_FILE
        config.PENDING_FILE = "pending_test.json"

        try:
            # Reset
            if os.path.exists(config.PENDING_FILE):
                os.remove(config.PENDING_FILE)

            # Test add
            pending_queue.add("/tmp/file1.txt")
            pending_queue.add("/tmp/file2.txt")
            pending_queue.add("/tmp/file1.txt")  # Duplicate — không được thêm 2 lần

            count = pending_queue.count()
            if count == 2:
                _ok("add() — không trùng lặp", f"{count} file")
            else:
                _fail("add() — không trùng lặp", f"expect 2, got {count}")

            all_q = pending_queue.get_all()
            if "/tmp/file1.txt" in all_q and "/tmp/file2.txt" in all_q:
                _ok("get_all() — đúng nội dung")
            else:
                _fail("get_all() — đúng nội dung")

            # Test remove
            pending_queue.remove("/tmp/file1.txt")
            count2 = pending_queue.count()
            if count2 == 1:
                _ok("remove() — giảm đúng", f"{count2} file còn lại")
            else:
                _fail("remove() — giảm đúng", f"expect 1, got {count2}")

            # Persistent: kiểm tra file JSON tồn tại
            if os.path.exists(config.PENDING_FILE):
                _ok("persistent — file JSON tồn tại")
                with open(config.PENDING_FILE) as f:
                    data = json.load(f)
                _ok("persistent — JSON hợp lệ", str(data))
            else:
                _fail("persistent — file JSON tồn tại")

        finally:
            # Dọn dẹp
            if os.path.exists(config.PENDING_FILE):
                os.remove(config.PENDING_FILE)
            config.PENDING_FILE = orig_pending
            if os.path.exists(backup_file):
                shutil.copy2(backup_file, config.PENDING_FILE)
                os.remove(backup_file)

    except Exception as e:
        _fail("pending_queue — exception", str(e))
        traceback.print_exc()


# =============================================================================
# 5. FTP UPLOADER (cần ftp_server_demo chạy)
# =============================================================================
def test_ftp(run_ftp=False):
    section("5. FTP Uploader")

    if not run_ftp:
        _skip("FTP test", "dùng --ftp để bật (tự khởi động FTP server demo)")
        return

    ftp_server_thread = None
    try:
        # Khởi động FTP server demo nội bộ trong thread
        import config
        from modules import settings_manager

        print(f"  {DIM('Đang khởi động FTP server demo nội bộ...')}")

        def _run_ftp_server():
            import os as _os
            _os.makedirs("./ftp_root", exist_ok=True)
            from pyftpdlib.handlers import FTPHandler
            from pyftpdlib.servers import FTPServer
            from pyftpdlib.authorizers import DummyAuthorizer

            authorizer = DummyAuthorizer()
            authorizer.add_user("testuser", "testpass", "./ftp_root", perm="elradfmwMT")
            handler = FTPHandler
            handler.authorizer = authorizer
            handler.passive_ports = range(60100, 60200)
            server = FTPServer(("127.0.0.1", 2122), handler)
            server.serve_forever()

        ftp_server_thread = threading.Thread(target=_run_ftp_server, daemon=True)
        ftp_server_thread.start()
        time.sleep(1.5)  # Chờ server sẵn sàng

        # Override settings để trỏ vào FTP demo
        orig_settings = settings_manager.load().copy()
        test_settings_data = dict(orig_settings)
        test_settings_data["ftp_host"] = "127.0.0.1"
        test_settings_data["ftp_port"] = 2122
        test_settings_data["ftp_user"] = "testuser"
        test_settings_data["ftp_pass"] = "testpass"
        settings_manager._cache = test_settings_data

        from modules import ftp_uploader, pending_queue

        # Tạo file test
        test_file = "data/test_ftp_upload.txt"
        os.makedirs("data", exist_ok=True)
        with open(test_file, "w") as f:
            f.write(f"FTP Test Upload — {datetime.now()}\n")

        # Test upload
        orig_pending = config.PENDING_FILE
        config.PENDING_FILE = "pending_ftp_test.json"
        if os.path.exists(config.PENDING_FILE):
            os.remove(config.PENDING_FILE)

        try:
            ftp_uploader.upload_new(test_file)
            remaining = pending_queue.count()
            if remaining == 0:
                _ok("upload_new() — upload thành công, pending=0")
            else:
                _fail("upload_new() — upload thành công", f"pending còn {remaining}")

            # Kiểm tra file có trong ftp_root không
            dest = os.path.join("ftp_root", os.path.basename(test_file))
            if os.path.exists(dest):
                _ok("file xuất hiện trong ftp_root/")
            else:
                _fail("file xuất hiện trong ftp_root/")

        finally:
            if os.path.exists(config.PENDING_FILE):
                os.remove(config.PENDING_FILE)
            config.PENDING_FILE = orig_pending
            if os.path.exists(test_file):
                os.remove(test_file)
            # Khôi phục settings
            settings_manager._cache = orig_settings

    except Exception as e:
        _fail("ftp_uploader — exception", str(e))
        traceback.print_exc()


# =============================================================================
# 6. MQTT PUBLISHER
# =============================================================================
def test_mqtt(run_mqtt=False):
    section("6. MQTT Publisher")

    if not run_mqtt:
        _skip("MQTT publish test", "dùng --mqtt để bật (cần broker online)")
        return

    try:
        import config
        from modules import settings_manager, mqtt_publisher

        s = settings_manager.load()
        print(f"  {DIM('Broker: ' + s['mqtt_host'] + ':' + str(s['mqtt_port']))}")
        print(f"  {DIM('Topic : ' + s['mqtt_topic'])}")

        # Dữ liệu test
        config.DEMO_MODE = True
        from modules import modbus_reader
        modbus_reader._last_dummy = {}
        record = modbus_reader.read_data()

        # Dùng pending file tạm
        orig_file = mqtt_publisher.PENDING_MQTT_FILE
        mqtt_publisher.PENDING_MQTT_FILE = "pending_mqtt_test.json"
        if os.path.exists(mqtt_publisher.PENDING_MQTT_FILE):
            os.remove(mqtt_publisher.PENDING_MQTT_FILE)

        try:
            mqtt_publisher.publish_new(record)
            remaining = mqtt_publisher.count_pending()
            if remaining == 0:
                _ok("publish_new() — publish thành công, pending=0")
            else:
                _fail("publish_new() — broker không phản hồi?",
                      f"pending còn {remaining} record")
                # In payload để debug
                item = mqtt_publisher._record_to_serializable(record)
                payload = mqtt_publisher._serializable_to_payload(item)
                print(f"  {DIM('Payload: ' + json.dumps(payload, indent=4, ensure_ascii=False))}")
        finally:
            if os.path.exists(mqtt_publisher.PENDING_MQTT_FILE):
                os.remove(mqtt_publisher.PENDING_MQTT_FILE)
            mqtt_publisher.PENDING_MQTT_FILE = orig_file

    except Exception as e:
        _fail("mqtt_publisher — exception", str(e))
        traceback.print_exc()


# =============================================================================
# 7. WATCHDOG
# =============================================================================
def test_watchdog():
    section("7. Watchdog")
    try:
        from modules import watchdog
        import io
        import logging

        # Bắt log output
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.DEBUG)
        logging.getLogger("modules.watchdog").addHandler(handler)
        logging.getLogger("modules.watchdog").setLevel(logging.DEBUG)

        watchdog.check_disk()
        _ok("check_disk() — không crash")

        watchdog.check_memory()
        _ok("check_memory() — không crash")

        watchdog.check_pending()
        _ok("check_pending() — không crash")

        watchdog.run_all()
        _ok("run_all() — không crash")

        log_output = log_capture.getvalue()
        if "Disk OK" in log_output or "DISK" in log_output:
            _ok("check_disk() — log hợp lệ")
        else:
            _ok("check_disk() — log (không bắt được, debug level)")

    except Exception as e:
        _fail("watchdog — exception", str(e))
        traceback.print_exc()


# =============================================================================
# 8. VÒNG LẶP TÍCH HỢP (Integration test không cần GUI)
# =============================================================================
def test_integration_loop():
    section("8. Integration Loop (5 chu kỳ, không GUI)")
    try:
        import config
        config.DEMO_MODE = True

        from modules import modbus_reader, file_writer, pending_queue, settings_manager
        modbus_reader._last_dummy = {}

        # Dùng thư mục data tạm
        orig_data_dir = config.DATA_DIR
        orig_pending  = config.PENDING_FILE
        config.DATA_DIR    = "data_test_headless"
        config.PENDING_FILE = "pending_test_integration.json"
        os.makedirs(config.DATA_DIR, exist_ok=True)

        try:
            last_record = None
            files_written = []
            errors = []

            for cycle in range(1, 6):
                record = modbus_reader.read_data()
                if record is None:
                    errors.append(f"Chu kỳ {cycle}: modbus_reader trả None")
                    continue
                last_record = record

                # Dùng timestamp khác nhau để tránh trùng tên file
                from datetime import timedelta
                record["timestamp"] = record["timestamp"] + timedelta(seconds=cycle)

                filepath = file_writer.write_file(record)
                if filepath is None:
                    errors.append(f"Chu kỳ {cycle}: file_writer trả None")
                    continue
                files_written.append(filepath)

                # Giả lập pending (không upload thật)
                pending_queue.add(filepath)

                vals = record["values"]
                ph   = vals.get("pH",  {}).get("value", "N/A")
                tss  = vals.get("TSS", {}).get("value", "N/A")
                temp = vals.get("Temp", {}).get("value", "N/A")
                print(f"  {DIM(f'Chu ky {cycle}: pH={ph}  TSS={tss}  Temp={temp}C')}")
                time.sleep(0.05)

            if len(files_written) == 5:
                _ok("5/5 chu kỳ ghi file thành công", f"{len(files_written)} files")
            else:
                _fail("5/5 chu kỳ ghi file", f"chỉ {len(files_written)}/5")

            count_q = pending_queue.count()
            if count_q == 5:
                _ok("pending queue đúng", f"{count_q} file chờ")
            else:
                _fail("pending queue đúng", f"expect 5, got {count_q}")

            if errors:
                for e in errors:
                    _fail("integration error", e)
            else:
                _ok("không có lỗi nào trong 5 chu kỳ")

        finally:
            # Dọn dẹp
            shutil.rmtree(config.DATA_DIR, ignore_errors=True)
            if os.path.exists(config.PENDING_FILE):
                os.remove(config.PENDING_FILE)
            config.DATA_DIR    = orig_data_dir
            config.PENDING_FILE = orig_pending

    except Exception as e:
        _fail("integration_loop — exception", str(e))
        traceback.print_exc()


# =============================================================================
# 9. MQTT PAYLOAD BUILDER (kiểm tra payload không cần gửi thật)
# =============================================================================
def test_mqtt_payload():
    section("9. MQTT Payload Builder (không gửi thật)")
    try:
        import config
        config.DEMO_MODE = True

        from modules import modbus_reader, mqtt_publisher, settings_manager
        modbus_reader._last_dummy = {}

        record = modbus_reader.read_data()
        item = mqtt_publisher._record_to_serializable(record)
        payload = mqtt_publisher._serializable_to_payload(item)

        expected_fields = [
            "ser_gw", "ser_dev", "time",
            "ph", "tss", "temp", "nh4",
            "flow_in", "flow_out",
            "total_in", "total_out",
            "temp_iscan", "cod",
        ]
        missing = [f for f in expected_fields if f not in payload]
        if missing:
            _fail("payload có đủ fields", f"thiếu: {missing}")
        else:
            _ok("payload có đủ fields", f"{len(expected_fields)} fields")

        s = settings_manager.load()
        if payload.get("ser_gw") == s.get("gateway_id"):
            _ok("ser_gw khớp gateway_id", payload["ser_gw"])
        else:
            _fail("ser_gw khớp gateway_id",
                  f"got '{payload.get('ser_gw')}' vs '{s.get('gateway_id')}'")

        # Kiểm tra giá trị là số
        numeric_fields = ["ph", "tss", "temp", "nh4", "flow_in", "flow_out",
                          "total_in", "total_out", "temp_iscan", "cod"]
        for f in numeric_fields:
            v = payload.get(f)
            if isinstance(v, (int, float)):
                _ok(f"  {f} = {v}")
            else:
                _fail(f"  {f}", f"không phải số: {v!r}")

        print(f"\n  {BOLD('JSON payload mẫu:')}")
        print("  " + json.dumps(payload, indent=4, ensure_ascii=False).replace("\n", "\n  "))

    except Exception as e:
        _fail("mqtt_payload_builder — exception", str(e))
        traceback.print_exc()


# =============================================================================
# 10. KIỂM TRA DEPENDENCIES
# =============================================================================
def test_dependencies():
    section("10. Kiểm tra Dependencies")
    deps = {
        "pymodbus":    "pymodbus",
        "paho-mqtt":   "paho.mqtt.client",
        "psutil":      "psutil",
        "pyftpdlib":   "pyftpdlib",
    }
    for display_name, import_name in deps.items():
        try:
            __import__(import_name)
            mod = sys.modules[import_name]
            ver = getattr(mod, "__version__", "?")
            _ok(f"{display_name}", f"v{ver}")
        except ImportError as e:
            _fail(f"{display_name}", f"CHƯA CÀI — pip install {display_name}")

    # PyQt5 — optional (không cần cho headless)
    try:
        import importlib
        spec = importlib.util.find_spec("PyQt5")
        if spec:
            _ok("PyQt5 (optional)", "đã cài — GUI có thể chạy")
        else:
            _skip("PyQt5 (optional)", "chưa cài — OK cho headless test")
    except Exception:
        _skip("PyQt5 (optional)", "không kiểm tra được")


# =============================================================================
# TỔNG KẾT
# =============================================================================
def print_summary():
    print(f"\n{BOLD('═' * 55)}")
    print(BOLD("  KẾT QUẢ TEST"))
    print(BOLD('═' * 55))

    passed  = [r for r in _results if r[1] is True]
    failed  = [r for r in _results if r[1] is False]
    skipped = [r for r in _results if r[1] is None]

    total = len(passed) + len(failed)

    print(f"  {GREEN('✔ PASS')}  : {len(passed):>3}")
    print(f"  {RED('✘ FAIL')}  : {len(failed):>3}")
    print(f"  {YELLOW('– SKIP')}  : {len(skipped):>3}")
    print(f"  {'TOTAL'}  : {total:>3}")
    print(BOLD('═' * 55))

    if failed:
        print(f"\n{RED(BOLD('  Các test THẤT BẠI:'))}")
        for name, _, msg in failed:
            print(f"    {RED('•')} {name}" + (f": {msg}" if msg else ""))

    overall = len(failed) == 0
    status  = GREEN("✔ TẤT CẢ PASS") if overall else RED("✘ CÓ LỖI — xem chi tiết ở trên")
    print(f"\n  {BOLD(status)}\n")
    return 0 if overall else 1


# =============================================================================
# MAIN
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Headless test cho project boxdata (không cần GUI)")
    parser.add_argument("--mqtt", action="store_true",
                        help="Bật test MQTT thật (cần broker online)")
    parser.add_argument("--ftp",  action="store_true",
                        help="Bật test FTP (tự khởi động ftp_server_demo nội bộ)")
    parser.add_argument("--all",  action="store_true",
                        help="Chạy tất cả test kể cả MQTT và FTP")
    args = parser.parse_args()

    run_mqtt = args.mqtt or args.all
    run_ftp  = args.ftp  or args.all

    print(BOLD(CYAN(
        "\n+----------------------------------------------+\n"
        "|   BOXDATA -- Headless Test Suite            |\n"
        "|   Chay khong can PyQt5 / man hinh           |\n"
        "+----------------------------------------------+"
    )))
    print(f"  Thời gian : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Thư mục   : {PROJECT_ROOT}")
    print(f"  MQTT test : {'BẬT' if run_mqtt else 'tắt (--mqtt để bật)'}")
    print(f"  FTP  test : {'BẬT' if run_ftp  else 'tắt (--ftp  để bật)'}")

    test_dependencies()
    test_settings()
    test_modbus_reader()
    test_file_writer()
    test_pending_queue()
    test_ftp(run_ftp=run_ftp)
    test_mqtt(run_mqtt=run_mqtt)
    test_watchdog()
    test_integration_loop()
    test_mqtt_payload()

    return print_summary()


if __name__ == "__main__":
    sys.exit(main())
