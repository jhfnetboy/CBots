from flask import Flask, render_template, request, jsonify
import asyncio
import schedule
import time
from datetime import datetime
from bot import TelegramBot
from config import HOST, PORT

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

if __name__ == '__main__':
    # Start the bot
    asyncio.run(bot.start())
    
    # Start the scheduler in a separate thread
    import threading
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.start()
    
    # Start the Flask app
    app.run(host=HOST, port=PORT) 