# PythonAnywhere Webhook compatible web_service.py
from flask import Flask, render_template, jsonify, request, Response
import logging
import os
import traceback
from dotenv import load_dotenv
import telegram # Import telegram library
from bot_api_core import BotAPICore # Import our BotAPICore

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Bot Initialization ---
try:
    bot_core = BotAPICore() # Instantiate the bot core
    VERSION = bot_core.version # Get version from bot core
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

# Configure app
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key')
app.config['JSON_AS_ASCII'] = False

# --- Webhook Route ---
# This route will be called by Telegram when new updates arrive
@app.route(f'/{bot_core.token}', methods=['POST']) # Route uses the bot token
def webhook_handler():
    if bot_core:
        try:
            update_json = request.get_json(force=True)
            update = telegram.Update.de_json(update_json, bot_core.updater.bot)
            # Process the update using the bot's dispatcher
            bot_core.updater.dispatcher.process_update(update)
            return Response(status=200) # Must return 200 OK to Telegram
        except Exception as e:
            logger.error(f"Error processing webhook update: {e}")
            logger.error(traceback.format_exc())
            return Response("Error processing update", status=500)
    else:
        logger.error("Bot core not initialized, cannot process webhook.")
        return Response("Bot not initialized", status=500)
# --------------------

# --- Other Routes (e.g., status page) ---
@app.route('/')
def index():
    """Homepage route - displays bot status and version"""
    return render_template('status.html', version=VERSION)

@app.route('/status')
def status():
    """Service status check"""
    bot_status = "Initialized" if bot_core else "Initialization Failed"
    return jsonify({
        "success": True,
        "version": VERSION,
        "bot_status": bot_status
    })
# ------------------------------------

# --- Error Handling ---
@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    logger.error(traceback.format_exc())
    return jsonify({"error": "Internal server error", "details": str(e)}), 500
# ---------------------

# Note: Removed the if __name__ == '__main__': block.
# The Flask app will be run by the WSGI server (e.g., on PythonAnywhere). 