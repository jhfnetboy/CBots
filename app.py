from flask import Flask, render_template, request, jsonify
import asyncio
import schedule
import time
from datetime import datetime
from bot import TelegramBot
from config import HOST, PORT
import threading
import nest_asyncio

app = Flask(__name__)
bot = TelegramBot()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
async def send_message():
    data = request.json
    message = data.get('message')
    target = data.get('target')
    schedule_time = data.get('schedule')

    if not message:
        return jsonify({'message': 'Message is required'}), 400

    try:
        if schedule_time:
            # Schedule the message
            schedule_time = datetime.fromisoformat(schedule_time)
            schedule.every().day.at(schedule_time.strftime('%H:%M')).do(
                asyncio.run, bot.send_message(message, target)
            )
            return jsonify({'message': 'Message scheduled successfully'})
        else:
            # Send immediately
            await bot.send_message(message, target)
            return jsonify({'message': 'Message sent successfully'})
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'}), 500

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(bot.start())
        loop.run_until_complete(bot.client.run_until_disconnected())
    except Exception as e:
        print(f"Error in bot thread: {e}")
    finally:
        loop.close()

if __name__ == '__main__':
    # Start the bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Start the Flask app
    app.run(host=HOST, port=PORT) 