import os
import logging
import random
import string
from telegram import Update, ChatPermissions
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

logger = logging.getLogger(__name__)

# Generate a random daily password
def generate_daily_password() -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(8))

class BotAPICore:
    def __init__(self):
        # Load token and group config
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable")
        self.target_group = os.getenv('TELEGRAM_GROUP')
        self.daily_password = generate_daily_password()
        self.version = "0.8.7" # Update version for Bot API migration
        self.token = token

        # Initialize Updater and dispatcher
        # Note: We don't start polling or webhook here.
        # That will be handled by the entry point (main.py or web_service.py via WSGI).
        self.updater = Updater(token=self.token, use_context=True)
        dp = self.updater.dispatcher

        # Register command handlers
        dp.add_handler(CommandHandler('pass', self.pass_command))
        dp.add_handler(CommandHandler('version', self.version_command))

        # Mute new members event
        dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, self.new_member_handler))

        # Private message handler for password validation
        dp.add_handler(MessageHandler(Filters.private & ~Filters.command, self.private_message_handler))
        
        logger.info("BotAPICore initialized with handlers.")

    # Removed the start() method as it's no longer needed here.
    # Startup (polling or webhook) is handled by the calling script.

    def pass_command(self, update: Update, context: CallbackContext):
        """Handle /pass command, send daily password"""
        text = f"今日密码是: {self.daily_password}\n请私聊此密码以解除禁言。"
        update.message.reply_text(text)
        logger.info(f"Sent daily password to {update.effective_user.first_name}")

    def version_command(self, update: Update, context: CallbackContext):
        """Handle /version command, send bot version"""
        update.message.reply_text(f"当前版本: {self.version}")
        logger.info(f"Sent version info to {update.effective_user.first_name}")

    def new_member_handler(self, update: Update, context: CallbackContext):
        """Handle new members joining the group, mute them"""
        chat_id = update.effective_chat.id
        for member in update.message.new_chat_members:
            try:
                permissions = ChatPermissions(can_send_messages=False)
                context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=member.id,
                    permissions=permissions
                )
                welcome = (
                    f"欢迎 {member.first_name} 加入群组!\n"
                    f"今日密码是: {self.daily_password}\n请私聊此密码以解除禁言。"
                )
                # Send welcome message to the group
                context.bot.send_message(chat_id=chat_id, text=welcome)
                logger.info(f"Muted new member {member.id} in chat {chat_id} and sent welcome message")
            except Exception as e:
                logger.error(f"Error muting new member {member.id} in chat {chat_id}: {e}")

    def private_message_handler(self, update: Update, context: CallbackContext):
        """Handle private messages for password validation"""
        text = update.message.text or ''
        user = update.effective_user
        if text == self.daily_password:
            if not self.target_group:
                 update.message.reply_text("错误：管理员未配置目标群组，无法解禁。")
                 logger.error(f"Cannot unmute user {user.id} because TELEGRAM_GROUP is not set.")
                 return
            try:
                # Try to parse target_group as int (ID) or use as str (username)
                try:
                    chat_id_to_unmute = int(self.target_group)
                except ValueError:
                    chat_id_to_unmute = self.target_group # Assume it's @username
                    
                permissions = ChatPermissions(can_send_messages=True, can_send_media_messages=True, 
                                          can_send_other_messages=True, can_add_web_page_previews=True)
                context.bot.restrict_chat_member(
                    chat_id=chat_id_to_unmute,
                    user_id=user.id,
                    permissions=permissions
                )
                update.message.reply_text("密码正确，已在目标群组解除禁言。")
                logger.info(f"Unmuted user {user.id} in target group {self.target_group}")
            except Exception as e:
                update.message.reply_text("在目标群组解禁失败，请联系管理员。")
                logger.error(f"Error unmuting user {user.id} in group {self.target_group}: {e}")
        else:
            update.message.reply_text("密码错误或非密码消息。请发送今日密码来解除禁言。") 