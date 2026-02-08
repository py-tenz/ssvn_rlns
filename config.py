import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")  # optional

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "pilot_training")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

# Normalize ADMIN_ID
try:
    ADMIN_ID = int(ADMIN_ID) if ADMIN_ID else None
except ValueError:
    ADMIN_ID = None
