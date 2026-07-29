import os
from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")

PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")

ADMIN_ID = int(os.getenv("ADMIN_ID"))

CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

PRICE = int(os.getenv("PRICE", 130000))