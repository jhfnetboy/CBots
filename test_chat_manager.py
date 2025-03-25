import asyncio
import logging
from chat_manager import ChatManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_chat_manager():
    try:
        # Create and initialize chat manager
        manager = ChatManager()
        await manager.initialize()
        
        # Get list of chats
        chats = manager.get_chat_list()
        logger.info("\nAvailable chats:")
        for chat in chats:
            logger.info(f"Chat: {chat['title']} (ID: {chat['id']})")
            
        # Close connection
        await manager.close()
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)

if __name__ == '__main__':
    asyncio.run(test_chat_manager()) 