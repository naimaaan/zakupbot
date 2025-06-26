import asyncio
import nest_asyncio
from bot.email import get_email as get_email_for_user, send_email_with_attachment
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from bot.handlers import register_handlers
from config.settings import get_settings
from bot.subscription import load_subscriptions
from bot.notifier import (
    download_excel_file,
    filter_excel_by_tru,
    TRU_CODES,
    DURATION_TYPE_MAP,
    TYPE_MAP,
    load_notified_uids,
    save_notified_uids,
    extract_tru_rows,
    load_tru_history,
    save_tru_history
)
from data_sources.test_api_fetch import fetch_procurement_plans
import os
import shutil

nest_asyncio.apply()

async def periodic_check(app):
    while True:
        await asyncio.sleep(1800)
        print("⏰ Автоматическая проверка закупок...")

        plans = await asyncio.to_thread(fetch_procurement_plans)
        notified_uids = load_notified_uids()
        tru_history = load_tru_history()  # 👈 Загружаем историю ТРУ
        new_uids = set()

        for plan in plans:
            uid = plan.get("excelFileUid")
            if not uid or uid in notified_uids:
                continue

            print(f"🆕 Проверка UID: {uid}")

            file_path = await asyncio.to_thread(download_excel_file, uid)
            if not file_path:
                continue

            filtered_path = await asyncio.to_thread(filter_excel_by_tru, file_path, TRU_CODES)
            os.remove(file_path)

            if not filtered_path:
                new_uids.add(uid)
                continue

            # 👇 Новая логика: сравниваем строки ТРУ
            customer_bin = plan.get("customerIdentifier", "UNKNOWN")
            tru_rows = await asyncio.to_thread(extract_tru_rows, filtered_path)

            if not tru_rows:
                new_uids.add(uid)
                os.remove(filtered_path)
                continue

            previous_rows = set(tru_history.get(customer_bin, []))
            new_rows = [row for row in tru_rows if row not in previous_rows]

            if not new_rows:
                print(f"🔁 Нет новых ТРУ строк для БИН {customer_bin}")
                new_uids.add(uid)
                os.remove(filtered_path)
                continue

            # Обновляем историю
            tru_history[customer_bin] = list(previous_rows.union(tru_rows))
            save_tru_history(tru_history)

            # 📩 Сообщение
            raw_date = plan.get("approveDate")
            date_time = datetime.fromtimestamp(raw_date / 1000).strftime("%Y-%m-%d %H:%M") if raw_date else "—"
            customer = plan.get("customerName", "—")
            year = plan.get("year", "—")
            duration_type = DURATION_TYPE_MAP.get(plan.get("planDurationType", "—"), "—")
            plan_type = TYPE_MAP.get(plan.get("planType", "—"), "—")

            message = (
                f"🏢  {customer}\n"
                f"📌  БИН: {customer_bin}\n"
                f"📅  {date_time}\n"
                f"📋  {duration_type} | {plan_type} | {year}\n"
                f"🔧  ТРУ: Услуги по обеспечению информационной безопасности.\n"
                f"🌐  Источник: zakup.sk.kz\n"
            )

            for user_id in load_subscriptions():
                try:
                    user = await app.bot.get_chat(user_id)
                    if not user:
                        continue

                    keyboard = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📥 Скачать ПЗ", callback_data=f"download_{uid}"),
                            InlineKeyboardButton("✉️ Отправить на почту", callback_data=f"email_{uid}")
                        ]
                    ])

                    await app.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        reply_markup=keyboard,
                        parse_mode="Markdown"
                    )
                    print(f"✅ Уведомление отправлено пользователю {user_id}")

                    email = get_email_for_user(user_id)
                    if email:
                        safe_customer = "".join(c for c in customer if c.isalnum() or c in " _-").strip().replace(" ", "_")
                        safe_bin = "".join(c for c in customer_bin if c.isalnum())
                        safe_duration = duration_type.replace(" ", "_") if duration_type else "Unknown"
                        safe_type = plan_type.replace(" ", "_") if plan_type else "Unknown"

                        new_filename = f"{safe_customer}_{safe_bin}_{safe_duration}_{safe_type}.xlsx"
                        new_filepath = os.path.join(os.path.dirname(filtered_path), new_filename)
        

                        shutil.copy(filtered_path, new_filepath)

                        try:
                            await asyncio.to_thread(send_email_with_attachment, email, new_filepath, message)
                            print(f"📧 Email отправлен на {email}")
                        except Exception as e:
                            print(f"❌ Ошибка при отправке email {email}: {e}")
                        finally:
                            if os.path.exists(new_filepath):
                                os.remove(new_filepath)
                except Exception as e:
                    print(f"❌ Ошибка отправки пользователю {user_id}: {e}")

            new_uids.add(uid)
            os.remove(filtered_path)

        if new_uids:
            notified_uids.update(new_uids)
            save_notified_uids(notified_uids)

async def run_bot():
    print("✅ Бот запущен.")
    settings = get_settings()

    if not settings.BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN не задан в .env или окружении.")

    app = ApplicationBuilder().token(settings.BOT_TOKEN).build()
    register_handlers(app)

    # 🔁 Запускаем фоновую проверку
    asyncio.create_task(periodic_check(app))

    await app.run_polling(close_loop=False)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_bot())
    except KeyboardInterrupt:
        print("⛔ Бот остановлен пользователем.")
