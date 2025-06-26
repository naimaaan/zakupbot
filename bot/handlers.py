import os
import re
import asyncio
from bot.access_control import access_required
import shutil
from bot.notifier import filter_excel_by_tru, TRU_CODES
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    MessageHandler,
    Application,
    filters
)
from bot.notifier import get_procurement_summary, download_excel_file
from bot.users import log_user_id
from bot.email import save_email
from telegram.ext import ConversationHandler

WAITING_FOR_EMAIL = 1
@access_required
async def set_email_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✉️ Отправьте вашу почту для уведомлений:")
    return WAITING_FOR_EMAIL
@access_required
async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    email = update.message.text.strip()

    # Простейшая валидация
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await update.message.reply_text("❌ Похоже, это не email. Попробуйте ещё раз.")
        return WAITING_FOR_EMAIL

    save_email(user.id, email)
    await update.message.reply_text(f"✅ Почта {email} сохранена.")
    return ConversationHandler.END

from bot.email import get_email as get_email_for_user
from bot.email import send_email_with_attachment


@access_required
async def handle_email_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.data.replace("email_", "")
    user_id = query.from_user.id
    email = get_email_for_user(user_id)

    if not email:
        await query.message.reply_text("❌ Вы ещё не указали почту. Используйте команду /setemail.")
        return

    raw_file = await asyncio.to_thread(download_excel_file, uid)
    if not raw_file:
        await query.message.reply_text("❌ Не удалось скачать файл.")
        return

    filtered_file = await asyncio.to_thread(filter_excel_by_tru, raw_file, TRU_CODES, save_file=True)
    if not filtered_file:
        await query.message.reply_text("❌ В файле не найдено подходящих позиций.")
        os.remove(raw_file)
        return

    # --- New code for renaming ---
    # Extract customer and BIN from the message text
    import re

    match_customer = re.search(r"🏢\s+(.*)", query.message.text)
    match_bin = re.search(r"БИН:\s*([^\n]+)", query.message.text)
    match_type = re.search(r"\|\s*(.*?)\s*\|", query.message.text)
    match_duration = re.search(r"📋\s*(.*?)\s*\|", query.message.text)

    customer = match_customer.group(1).strip() if match_customer else "Customer"
    customer_bin = match_bin.group(1).strip() if match_bin else "BIN"
    plan_type = match_type.group(1).strip().replace(" ", "_") if match_type else "UnknownType"
    duration_type = match_duration.group(1).strip().replace(" ", "_") if match_duration else "UnknownDuration"

    safe_customer = "".join(c for c in customer if c.isalnum() or c in " _-").strip().replace(" ", "_")
    safe_bin = "".join(c for c in customer_bin if c.isalnum())

    new_filename = f"{safe_customer}_{safe_bin}_{duration_type}_{plan_type}.xlsx"
    new_filepath = os.path.join(os.path.dirname(filtered_file), new_filename)

    shutil.copy(filtered_file, new_filepath)
    # --- End new code ---

    try:
        await asyncio.to_thread(send_email_with_attachment, email, new_filepath, query.message.text)
        await query.message.reply_text(f"✅ Обработанный ПЗ отправлен на {email}")
    except Exception as e:
        await query.message.reply_text(f"❌ Ошибка при отправке на почту: {e}")
    finally:
        if raw_file and os.path.exists(raw_file):
            os.remove(raw_file)
        if filtered_file and os.path.exists(filtered_file):
            os.remove(filtered_file)
        if new_filepath and os.path.exists(new_filepath):
            os.remove(new_filepath)
@access_required
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_user_id(user.id, user.full_name)

    keyboard = [["/check"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "👋 Добро пожаловать в *ZakupBot*!\n\n"
        "Этот бот отслеживает обновления в планах закупок и уведомляет, если есть подходящие ТРУ.\n\n"
        "📌 Используйте /check чтобы проверить актуальные данные.\n"
        "🔧 Бот находится на стадии настройки и тестирования.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
@access_required
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Проверяю планы закупок, подождите...")
    summaries = await asyncio.to_thread(get_procurement_summary, TRU_CODES)

    if not summaries:
        await update.message.reply_text("🚫 Подходящих планов не найдено.")
        return

    for item in summaries:
        keyboard = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("📥 Скачать ПЗ", callback_data=f"download_{item['uid']}"),
        InlineKeyboardButton("📧 Отправить на почту", callback_data=f"email_{item['uid']}")
    ]
])

        await update.message.reply_text(
            item["text"],
            reply_markup=keyboard
        )

from telegram.ext import CallbackQueryHandler
@access_required
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_subscription(user_id)
    await update.message.reply_text("✅ Вы подписались на автоматические уведомления о новых закупках.")
@access_required
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    remove_subscription(user_id)
    await update.message.reply_text("❌ Вы отписались от автоматических уведомлений.")

@access_required
async def handle_download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.data.replace("download_", "")
    file_path = await asyncio.to_thread(download_excel_file, uid)

    if not file_path:
        await query.message.reply_text("❌ Не удалось скачать файл.")
        return

    # --- New code for renaming ---
    match_customer = re.search(r"🏢\s+(.*)", query.message.text)
    match_bin = re.search(r"БИН:\s*([^\n]+)", query.message.text)
    match_type = re.search(r"\|\s*(.*?)\s*\|", query.message.text)
    match_duration = re.search(r"📋\s*(.*?)\s*\|", query.message.text)

    customer = match_customer.group(1).strip() if match_customer else "Customer"
    customer_bin = match_bin.group(1).strip() if match_bin else "BIN"
    plan_type = match_type.group(1).strip().replace(" ", "_") if match_type else "UnknownType"
    duration_type = match_duration.group(1).strip().replace(" ", "_") if match_duration else "UnknownDuration"

    safe_customer = "".join(c for c in customer if c.isalnum() or c in " _-").strip().replace(" ", "_")
    safe_bin = "".join(c for c in customer_bin if c.isalnum())

    new_filename = f"{safe_customer}_{safe_bin}_{duration_type}_{plan_type}.xlsx"
    new_filepath = os.path.join(os.path.dirname(file_path), new_filename)

    shutil.copy(file_path, new_filepath)
    # --- End new code ---

    try:
        await context.bot.send_document(chat_id=query.message.chat_id, document=open(new_filepath, "rb"))
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        if new_filepath and os.path.exists(new_filepath):
            os.remove(new_filepath)

from telegram.ext import ConversationHandler
from bot.subscription import add_subscription, remove_subscription
def register_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("subscribe", subscribe))       # ✅ Добавил сюда
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))   # ✅ И сюда
    app.add_handler(CallbackQueryHandler(handle_download_callback, pattern=r"^download_"))
    app.add_handler(CallbackQueryHandler(handle_email_callback, pattern=r"^email_"))

    email_conv = ConversationHandler(
        entry_points=[CommandHandler("setemail", set_email_command)],
        states={WAITING_FOR_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)]},
        fallbacks=[],
    )
    app.add_handler(email_conv)
