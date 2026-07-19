"""ระบบ Logger ของโปรแกรม AI Live Streamer."""

import logging


LOGGER_NAME = "AI Live"


def setup_logger() -> logging.Logger:
    """สร้าง Logger และป้องกัน Handler ซ้ำ."""

    app_logger = logging.getLogger(LOGGER_NAME)
    app_logger.setLevel(logging.INFO)

    # ไม่ส่ง Log ต่อไปยัง Root Logger
    # ป้องกันข้อความเดียวกันแสดงสองครั้ง
    app_logger.propagate = False

    # ลบ Handler เดิมทั้งหมดก่อนตั้งค่าใหม่
    app_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(levelname)s : %(message)s"
    )

    console_handler.setFormatter(formatter)
    app_logger.addHandler(console_handler)

    return app_logger


logger = setup_logger()