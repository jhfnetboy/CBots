import asyncio
import logging
from app import start_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        logger.info("Starting application...")
        start_app()
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True) 