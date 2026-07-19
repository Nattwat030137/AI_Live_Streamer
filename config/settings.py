"""ค่าตั้งค่าหลักของโปรแกรม AI Live Streamer."""

import os
from pathlib import Path

from dotenv import load_dotenv


# ตำแหน่งโฟลเดอร์หลักของโปรเจกต์
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ตำแหน่งไฟล์ .env
ENV_FILE = PROJECT_ROOT / ".env"

# โหลดค่าจากไฟล์ .env
load_dotenv(dotenv_path=ENV_FILE)


# =========================================================
# ข้อมูลทั่วไปของโปรแกรม
# =========================================================

APP_NAME = "AI Live Streamer"
APP_VERSION = "0.0.1"
DEBUG_MODE = True


# =========================================================
# การตั้งค่า AI
# =========================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_MODEL = "กำหนดภายหลัง"


# =========================================================
# การตั้งค่าเสียง
# =========================================================

VOICE_LANGUAGE = "th-TH"
VOICE_SPEED = 1.0
VOICE_VOLUME = 1.0


# =========================================================
# การตั้งค่า OBS
# =========================================================

OBS_HOST = "localhost"
OBS_PORT = 4455