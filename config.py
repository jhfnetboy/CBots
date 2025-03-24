import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Web server configuration
HOST = 'localhost'
PORT = 8872

# Telegram channel/group configuration
TARGET_CHANNEL = os.getenv('TELEGRAM_CHANNEL')
TARGET_GROUP = os.getenv('TELEGRAM_GROUP')

# Bot configuration
BOT_USERNAME = os.getenv('BOT_USERNAME')
HELP_MESSAGE = """
Available commands:
/help - Show this help message
/content - Get content list
""" 