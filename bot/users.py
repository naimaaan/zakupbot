import os

ALLOWED_IDS = set("1082863162")  # Пока пусто — никого не блокируем

ID_LOG_FILE = "storage/users.txt"
os.makedirs("storage", exist_ok=True)

def log_user_id(user_id: int, full_name: str):
    # Если ID уже есть — не пишем дубликат
    if os.path.exists(ID_LOG_FILE):
        with open(ID_LOG_FILE, "r") as f:
            existing_ids = f.read()
        if str(user_id) in existing_ids:
            return

    with open(ID_LOG_FILE, "a") as f:
        f.write(f"{user_id}  # {full_name}\n")

def is_allowed_user(user_id: int) -> bool:
    return len(ALLOWED_IDS) == 0 or user_id in ALLOWED_IDS
