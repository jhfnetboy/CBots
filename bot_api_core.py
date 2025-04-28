import os
import logging
import random
import string
from telegram import Update, ChatPermissions
# Use ApplicationBuilder for initialization in PTB v20+
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
import traceback # Import traceback for detailed error logging

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
        # Update version for bilingual and unmute fix attempt
        self.version = "0.8.9" 
        self.token = token
        
        # Determine environment tag
        if os.getenv('PYTHONANYWHERE_DOMAIN'):
            self.environment_tag = "[PythonAnywhere]"
        else:
            self.environment_tag = "[LocalHost]"

        # Initialize Application using ApplicationBuilder (PTB v20+)
        application_builder = Application.builder().token(self.token)
        self.application = application_builder.build()

        # Register handlers directly on the application in PTB v20+
        self.application.add_handler(CommandHandler('pass', self.pass_command))
        self.application.add_handler(CommandHandler('version', self.version_command))
        self.application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.new_member_handler))
        self.application.add_handler(MessageHandler(filters.ChatType.PRIVATE & (~filters.COMMAND), self.private_message_handler))
        
        logger.info(f"BotAPICore {self.version} initialized ({self.environment_tag}) with handlers using ApplicationBuilder.")
        logger.info(f"Daily password generated: {self.daily_password}")
        logger.info(f"Target group for unmute: {self.target_group}")

    # --- Polling and Idle Methods (for local execution via main.py) ---
    def run_polling(self):
        """Starts the bot in polling mode and blocks until interrupted."""
        logger.info(f"Starting bot in polling mode ({self.environment_tag})...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Bot polling stopped.")

    def stop_polling(self):
        """Stops the polling loop if running."""
        # run_polling handles shutdown gracefully on SIGINT/SIGTERM
        # If we need manual stop: await self.application.shutdown()
        logger.info("Attempting to stop polling (usually handled by run_polling)...")
        # No explicit stop needed here if run_polling handles signals

    # --- Command Handlers ---
    # Make command handlers async
    async def pass_command(self, update: Update, context: CallbackContext):
        """Handle /pass command, send daily password (Bilingual + Env Tag)"""
        text = (
            f"今日密码是 (Today's password is): {self.daily_password}\n"
            f"请私聊此密码以解除禁言。(Please DM this password to the bot to unmute.)\n"
            f"服务来源 (Service Source): {self.environment_tag}"
        )
        try:
            await update.message.reply_text(text)
            logger.info(f"Sent daily password ({self.environment_tag}) to {update.effective_user.first_name}")
        except Exception as e:
            logger.error(f"Error replying to /pass command: {e}")

    async def version_command(self, update: Update, context: CallbackContext):
        """Handle /version command, send bot version (Bilingual + Env Tag)"""
        text = f"当前版本 (Current version): {self.version} {self.environment_tag}"
        try:
            await update.message.reply_text(text)
            logger.info(f"Sent version info ({self.environment_tag}) to {update.effective_user.first_name}")
        except Exception as e:
            logger.error(f"Error replying to /version command: {e}")

    # --- Event Handlers --- 
    # These were already async
    async def new_member_handler(self, update: Update, context: CallbackContext):
        """Handle new members joining the group, mute them (No welcome message)"""
        chat_id = update.effective_chat.id
        for member in update.message.new_chat_members:
            try:
                permissions = ChatPermissions(can_send_messages=False)
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=member.id,
                    permissions=permissions
                )
                # Removed welcome message sending
                logger.info(f"Muted new member {member.first_name} ({self.environment_tag}) in chat {chat_id}. Welcome message removed.")
            except Exception as e:
                # Log error with traceback
                logger.error(f"Error muting new member {member.id} in chat {chat_id}: {e}\n{traceback.format_exc()}")

    async def private_message_handler(self, update: Update, context: CallbackContext):
        """Handle private messages for password validation (Bilingual, detailed error log)"""
        text = update.message.text or ''
        user = update.effective_user
        logger.info(f"Received private message ({self.environment_tag}) from {user.first_name} (ID: {user.id}): '{text[:20]}...'")
        
        if text == self.daily_password:
            logger.info(f"Correct password received ({self.environment_tag}) from {user.first_name}. Attempting to unmute in target group: {self.target_group}")
            if not self.target_group:
                 reply_text = "错误：管理员未配置目标群组，无法解禁。(Error: Target group not configured by admin, cannot unmute.)"
                 await update.message.reply_text(reply_text)
                 logger.error(f"Cannot unmute user {user.id} because TELEGRAM_GROUP is not set.")
                 return
            try:
                # Try to parse target_group as int (ID) or use as str (username)
                try:
                    chat_id_to_unmute = int(self.target_group) # Assume it's a numeric ID first
                    logger.info(f"Target group '{self.target_group}' parsed as numeric ID: {chat_id_to_unmute}")
                except ValueError:
                    # If not numeric, assume it's a username like @groupname or groupname
                    chat_id_to_unmute = self.target_group 
                    logger.info(f"Target group '{self.target_group}' treated as username/link.")
                    # Prepending '@' might be necessary if it wasn't included, 
                    # but restrict_chat_member usually handles this. Let's try without first.
                    # if not chat_id_to_unmute.startswith('@'):
                    #     chat_id_to_unmute = '@' + chat_id_to_unmute
                    #     logger.info(f"Prepended '@', now using: {chat_id_to_unmute}")
                        
                # Correct Permissions for PTB v20+ to allow most message types
                permissions = ChatPermissions(
                    can_send_messages=True, 
                    can_send_audios=True,
                    can_send_documents=True,
                    can_send_photos=True,
                    can_send_videos=True,
                    can_send_video_notes=True,
                    can_send_voice_notes=True,
                    can_send_polls=True,
                    can_send_other_messages=True, # Allows stickers, gifs etc.
                    can_add_web_page_previews=True,
                    # Keep restrictions on admin-like actions
                    can_change_info=False,
                    can_invite_users=False,
                    can_pin_messages=False
                )
                
                logger.info(f"Calling restrict_chat_member for user {user.id} in chat {chat_id_to_unmute} with permissions: {permissions}")
                success = await context.bot.restrict_chat_member(
                    chat_id=chat_id_to_unmute,
                    user_id=user.id,
                    permissions=permissions
                )
                
                if success:
                    reply_text = "密码正确，已在目标群组解除禁言。(Password correct, you have been unmuted in the target group.)"
                    await update.message.reply_text(reply_text)
                    logger.info(f"Successfully unmuted user ({self.environment_tag}) {user.id} in target group {self.target_group}. API returned success.")
                else:
                    reply_text = "在目标群组解禁失败（API未返回成功）。请联系管理员。(Failed to unmute in target group (API did not return success). Please contact admin.)"
                    await update.message.reply_text(reply_text)
                    logger.warning(f"Failed to unmute user ({self.environment_tag}) {user.id} in group {self.target_group}. API returned non-success.")

            except Exception as e:
                reply_text = "在目标群组解禁失败。请联系管理员。(Failed to unmute in target group. Please contact admin.)"
                await update.message.reply_text(reply_text)
                logger.error(f"Error unmuting user ({self.environment_tag}) {user.id} in group {self.target_group}: {e}\n{traceback.format_exc()}")
        else:
            reply_text = (
                "密码错误或非密码消息。请发送今日密码以解除禁言。\n"
                "(Incorrect password or not a password message. Please send today's password to get unmuted.)"
            )
            await update.message.reply_text(reply_text)
            logger.info(f"Incorrect password ({self.environment_tag}) received from {user.first_name}.")

    # --- Webhook Integration Method (for web_service.py) ---
    async def process_update(self, update_data: dict):
        """Process a single update received via webhook."""
        logger.debug(f"Processing webhook update ({self.environment_tag})...")
        async with self.application:
            update = Update.de_json(update_data, self.application.bot)
            await self.application.process_update(update)
            logger.debug("Processed webhook update.") 