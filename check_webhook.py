import os
from telegram import Bot
from dotenv import load_dotenv

load_dotenv() # Load .env

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL') # 确保 .env 里有这个且正确

if not TOKEN or not WEBHOOK_URL:
    print("Error: TELEGRAM_BOT_TOKEN or WEBHOOK_URL not found in .env")
else:
    # 确保 URL 格式是 https://yourusername.pythonanywhere.com/BOT_TOKEN
    hook_url = f"{WEBHOOK_URL}/{TOKEN}"
    bot = Bot(token=TOKEN)
    try:
        # --- 关键步骤：调用 set_webhook ---
        success = await bot.set_webhook(url=hook_url)
        if success:
            print(f"Webhook set successfully to: {hook_url}")
        else:
             print(f"Webhook set failed (API returned False). URL: {hook_url}")
    except Exception as e:
        print(f"Error setting webhook: {e}")

# 如果在脚本里运行，需要用 asyncio.run()
# import asyncio
# asyncio.run(set_my_webhook()) # 假设你把上面的代码放进一个 async 函数