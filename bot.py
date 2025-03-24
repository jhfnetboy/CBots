from telethon import TelegramClient, events
from config import API_ID, API_HASH, HELP_MESSAGE, TARGET_CHANNEL, TARGET_GROUP, BOT_TOKEN

class TelegramBot:
    def __init__(self):
        print(f"Initializing bot with API_ID: {API_ID}")
        self.client = TelegramClient('bot_session', API_ID, API_HASH)
        self.setup_handlers()

    def setup_handlers(self):
        @self.client.on(events.NewMessage(incoming=True))
        async def my_event_handler(event):
            print("=== New Message Received ===")
            print(f"Message text: {event.text}")
            print(f"From user: {event.sender_id}")
            print(f"Chat: {event.chat_id}")
            print(f"Bot mentioned: {event.message.mentioned}")
            print("==========================")
            
            # 只响应被@的消息
            if event.message.mentioned:
                print("Bot was mentioned, responding...")
                if event.text.lower() == 'help':
                    await event.reply(HELP_MESSAGE)
                else:
                    await event.reply('I received your message!')
            else:
                print("Bot was not mentioned, ignoring message")

    async def send_message(self, message, target=None):
        if target is None:
            target = TARGET_CHANNEL
        print(f"Sending message to {target}: {message}")
        await self.client.send_message(target, message)

    async def start(self):
        print("Starting bot...")
        try:
            await self.client.start(bot_token=BOT_TOKEN)
            print("Bot started successfully!")
            me = await self.client.get_me()
            print(f"Bot is running as: {me}")
            print(f"Bot username: {me.username}")
            print(f"Bot ID: {me.id}")
            print("Bot is ready to receive messages!")
            
            # 测试发送消息
            print("Testing message sending...")
            await self.send_message("Bot is now online! (Only responds when mentioned)", TARGET_GROUP)
            print("Test message sent!")
            
        except Exception as e:
            print(f"Error starting bot: {e}")
            raise

    async def stop(self):
        print("Stopping bot...")
        await self.client.disconnect()
        print("Bot stopped!") 