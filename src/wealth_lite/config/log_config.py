import logging
import os
import glob
import time
from datetime import datetime

# 日志保留天数
LOG_RETENTION_DAYS = 30

# 日志级别（可由外部覆盖）
LOG_LEVEL = logging.DEBUG  # 可选: logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL

# 日志目录和文件名
LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/wealth_lite_{datetime.now().strftime('%Y%m%d')}.log"


def setup_logging(log_level=LOG_LEVEL):
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    cleanup_old_logs()


def cleanup_old_logs():
    now = time.time()
    for log_file in glob.glob(f"{LOG_DIR}/wealth_lite_*.log"):
        if os.path.isfile(log_file):
            mtime = os.path.getmtime(log_file)
            if now - mtime > LOG_RETENTION_DAYS * 86400:
                try:
                    os.remove(log_file)
                    logging.info(f"已自动删除过期日志文件: {log_file}")
                except Exception as e:
                    logging.warning(f"删除日志文件失败: {log_file}, 错误: {e}") 