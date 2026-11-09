# =============================================================================
# ftp_server_demo.py — FTP Server giả lập chạy local để test
# Chạy file này trên terminal riêng trước khi chạy main.py
# Thư mục nhận file: ./ftp_root/
# =============================================================================

import os
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer

FTP_PORT = 2121
FTP_USER = "databox"
FTP_PASS = "123456"
FTP_DIR  = "./ftp_root"

os.makedirs(FTP_DIR, exist_ok=True)

authorizer = DummyAuthorizer()
authorizer.add_user(FTP_USER, FTP_PASS, FTP_DIR, perm="elradfmwMT")

handler = FTPHandler
handler.authorizer = authorizer
handler.passive_ports = range(60000, 60100)

server = FTPServer(("127.0.0.1", FTP_PORT), handler)

print(f"FTP Server demo đang chạy tại ftp://127.0.0.1:{FTP_PORT}")
print(f"User: {FTP_USER} / Pass: {FTP_PASS}")
print(f"File nhận vào: {os.path.abspath(FTP_DIR)}")
print("Nhấn Ctrl+C để dừng.\n")

server.serve_forever()
