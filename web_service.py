# PythonAnywhere Webhook compatible web_service.py
from flask import Flask, render_template, jsonify, request, Response
import logging
import os
import sys # Import sys for stderr logging
import traceback
from dotenv import load_dotenv
import telegram # Import telegram library
from bot_api_core import BotAPICore # Import our BotAPICore
import asyncio # Needed for running async webhook processing
import time # Import time for timestamp

# Load environment variables
load_dotenv()

# --- Configure Logging EARLY --- 
# Log to stderr (goes to PythonAnywhere Error log) AND a file
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Get root logger or a specific one
logger.setLevel(logging.INFO) # Set desired log level

# File Handler (Use absolute path for PA)
log_file_path = '/home/jhfnetboy/dev-CBots/bot.log' # *** USE YOUR ACTUAL PATH ***
try:
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"Error setting up FileHandler for {log_file_path}: {e}") # Print error if file logging fails

# Stream Handler (to stderr for WSGI error log)
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

logger.info("--- web_service.py execution started --- ")
# -----------------------------

# --- Bot Initialization ---
logger.info("Initializing BotAPICore...")
try:
    bot_core = BotAPICore() # Instantiate the bot core
    VERSION = bot_core.version # Get version from bot core
    logger.info(f"BotAPICore version {VERSION} initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize BotAPICore: {e}")
    logger.error(traceback.format_exc())
    bot_core = None
    VERSION = "Error"
# ------------------------

# Create Flask app
app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
logger.info("Flask app created.")

# Configure app
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')
app.config['JSON_AS_ASCII'] = False

# --- Webhook Route ---
webhook_path = f'/{bot_core.token}' if bot_core else '/webhook-error-bot-not-init'
logger.info(f"Registering webhook handler at path: {webhook_path}")
@app.route(webhook_path, methods=['POST']) 
def webhook_handler():
    logger.info(f"Webhook received at {webhook_path}")
    if bot_core and hasattr(bot_core, 'process_update'):
        try:
            update_json = request.get_json(force=True, silent=True) # Use silent=True
            if not update_json:
                 logger.warning("Webhook received empty or non-JSON data.")
                 return Response(status=200) # Still return 200
            
            logger.info(f"Webhook JSON keys: {list(update_json.keys())}")
            # Run the async process_update function
            logger.debug("Calling asyncio.run(bot_core.process_update(...))")
            asyncio.run(bot_core.process_update(update_json))
            logger.info("Successfully processed webhook update via asyncio.run.")
            return Response(status=200) # Must return 200 OK to Telegram immediately
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")
            logger.error(traceback.format_exc())
            return Response(status=200) # Still return 200 to Telegram
    else:
        logger.error("Webhook received but Bot core not initialized or process_update missing.")
        return Response(status=200) # Still return 200
# --------------------

# --- Other Routes (e.g., status page) ---
@app.route('/')
def index():
    """Homepage route - displays bot status and version"""
    logger.debug("Request received for / route")
    return render_template('status.html', version=VERSION)

@app.route('/status')
def status():
    """Service status check - Simplified for Bot API mode"""
    logger.debug("Request received for /status route")
    bot_initialized = bot_core is not None
    bot_status = "Initialized" if bot_initialized else "Initialization Failed"
    # Simulate event loop status or indicate webhook mode
    event_loop_status = {
        "is_running": bot_initialized, # If bot is init, assume webhook is ready
        "mode": "Webhook (via WSGI)"
    }
    
    status_data = {
        "success": bot_initialized, # Success depends on bot initialization
        "version": VERSION,
        "bot_status": bot_status,
        # Mimic expected structure, even if simplified
        "event_loop": event_loop_status, 
        "time": time.time() # Add current timestamp
        # Add other relevant info if needed
        # "daily_password_set": hasattr(bot_core, 'daily_password') if bot_core else False,
        # "target_group_set": bool(getattr(bot_core, 'target_group', None)) if bot_core else False
    }
    logger.info(f"Returning status: {status_data}")
    return jsonify(status_data)
# ------------------------------------

# --- Error Handling ---
@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error (500 handler): {e}")
    logger.error(traceback.format_exc())
    return jsonify({"error": "Internal server error", "details": str(e)}), 500
# ---------------------

logger.info("--- web_service.py execution finished setup --- ")
# Note: The Flask app will be run by the WSGI server. 