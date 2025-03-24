from telethon import TelegramClient, events
from config import API_ID, API_HASH, HELP_MESSAGE, TARGET_CHANNEL, TARGET_GROUP

class TelegramBot:
    def __init__(self):
        self.client = TelegramClient('session_name', API_ID, API_HASH)
        self.setup_handlers()

    def setup_handlers(self):
        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            await event.respond(HELP_MESSAGE)

        @self.client.on(events.NewMessage(pattern='/content'))
        async def content_handler(event):
            # TODO: Implement content list
            await event.respond("Content list will be implemented soon!")

    async def send_message(self, message, target=None):
        if target is None:
            target = TARGET_CHANNEL
        await self.client.send_message(target, message)

    async def start(self):
        await self.client.start()
        print("Bot started!")

    async def stop(self):
        await self.client.disconnect()
        print("Bot stopped!") 