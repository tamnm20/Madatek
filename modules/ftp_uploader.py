# =============================================================================
# modules/ftp_uploader.py — Upload file lên FTP Server
# Đọc thông tin FTP từ settings.json thay vì config.py
# =============================================================================

import ftplib
import os
import logging
import time
import random
from modules import pending_queue
from modules import settings_manager

logger = logging.getLogger(__name__)

# Delay giữa các file khi retry (giây)
RETRY_DELAY_MIN = 2
RETRY_DELAY_MAX = 3


def _upload_one(filepath):
    if not os.path.exists(filepath):
        logger.warning("File không tồn tại, bỏ qua: %s", filepath)
        return True
    try:
        s = settings_manager.load()
        filename = os.path.basename(filepath)
        ftp = ftplib.FTP()
        ftp.connect(s["ftp_host"], int(s["ftp_port"]), timeout=10)
        ftp.login(s["ftp_user"], s["ftp_pass"])
        with open(filepath, "rb") as f:
            ftp.storbinary(f"STOR {filename}", f)
        ftp.quit()
        logger.info("Upload thành công: %s", filename)
        return True
    except Exception as e:
        logger.warning("Upload thất bại (%s): %s", filepath, e)
        return False


def upload_new(filepath):
    pending_queue.add(filepath)
    if _upload_one(filepath):
        pending_queue.remove(filepath)


def retry_pending():
    queue = pending_queue.get_all()
    if not queue:
        return
    logger.info("Đang retry %d file chờ upload...", len(queue))
    for filepath in queue:
        if _upload_one(filepath):
            pending_queue.remove(filepath)
            # Delay 2-3 giây giữa mỗi file để không spam server
            remaining = pending_queue.get_all()
            if remaining:
                delay = random.uniform(RETRY_DELAY_MIN, RETRY_DELAY_MAX)
                logger.debug("Chờ %.1fs trước khi gửi file tiếp theo...", delay)
                time.sleep(delay)
        else:
            # Upload thất bại → dừng retry, chờ lần sau
            break