import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Web server configuration
HOST = 'localhost'
PORT = 8872

# Telegram channel/group configuration
TARGET_CHANNEL = os.getenv('TELEGRAM_CHANNEL')
TARGET_GROUP = os.getenv('TELEGRAM_GROUP')

# Bot configuration
BOT_USERNAME = os.getenv('BOT_USERNAME')

# New user verification configuration
NEW_USER_VERIFICATION = {
    'enabled': True,
    'mute_duration': 4 * 60 * 60,  # 4 hours (in seconds)
    'message_length': {
        'min': 20,
        'max': 50
    }
}

# Command configuration
COMMANDS = {
    '/help': 'Show help message',
    '/content': 'Show content list',
    '/PNTs': 'Query PNTs information',
    '/hi': 'Say hello',
    '/price': 'Query price information',
    '/volume': 'Query volume information',
    '/market': 'Query market information',
    '/news': 'Query news information',
    '/stats': 'Query statistics information'
}

# 帮助消息
HELP_MESSAGE = """Available commands:
/help - Show this help message
/content - Show content list
/PNTs - Query PNTs information
/hi - Say hello
/price - Query price information
/volume - Query volume information
/market - Query market information
/news - Query news information
/stats - Query statistics information"""

# Twitter API Configuration
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Web Server Configuration
WEB_SERVER_CONFIG = {
    'host': '0.0.0.0',
    'port': 8872,
    'debug': True
}

# Telegram API Configuration
CONFIG = {
    'telegram': {
        'api_id': API_ID,
        'api_hash': API_HASH,
        'bot_token': BOT_TOKEN,
        'target_group': TARGET_GROUP,
    }
} 