import json
import os
import smtplib
from email.message import EmailMessage

NOTIFIED_FILE = "storage/notified_uids.json"

def load_notified_uids():
    if os.path.exists(NOTIFIED_FILE):
        with open(NOTIFIED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_notified_uids(uids):
    with open(NOTIFIED_FILE, "w") as f:
        json.dump(list(uids), f)

def send_email_with_attachment(to_email: str, file_path: str, message_text: str):
    # Настройки отправителя
    smtp_server = "mx1.qazcloud.kz"
    smtp_port = 587
    sender_email = os.getenv("sender_email")
    sender_password = os.getenv("sender_password")  # пароль приложения Gmail

    msg = EmailMessage()
    msg["Subject"] = "План закупок"
    msg["From"] = sender_email
    msg["To"] = to_email

    # Используем текст с описанием компании
    msg.set_content(
        message_text + "\n\nВо вложении находится отфильтрованный план закупок"
    )

    # Присоединить файл
    with open(file_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(file_path)
        msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=file_name)

    # Отправка письма
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)

STORAGE_FILE = "storage/emails.json"
os.makedirs("storage", exist_ok=True)

def load_emails():
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_email(user_id: int, email: str):
    data = load_emails()
    data[str(user_id)] = email
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_email(user_id: int) -> str | None:
    data = load_emails()
    return data.get(str(user_id))
