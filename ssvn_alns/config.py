from argparse import ArgumentError
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
MYSQL_PASS = os.getenv("MYSQL_PASS")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")