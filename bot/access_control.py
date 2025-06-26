# bot/access_control.py

from config.settings import get_settings
from telegram import Update
from telegram.ext import ContextTypes

settings = get_settings()

def access_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user and user.id in settings.ALLOWED_USERS:
            return await func(update, context)
        else:
            await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
    return wrapper
