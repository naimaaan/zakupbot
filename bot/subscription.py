import json
import os

SUBS_FILE = "storage/subscribed.json"
os.makedirs("storage", exist_ok=True)

def load_subscriptions() -> set:
    if not os.path.exists(SUBS_FILE):
        return set()
    with open(SUBS_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))

def save_subscriptions(subs: set):
    with open(SUBS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(subs), f, indent=2)

def add_subscription(user_id: int):
    subs = load_subscriptions()
    subs.add(user_id)
    save_subscriptions(subs)

def remove_subscription(user_id: int):
    subs = load_subscriptions()
    subs.discard(user_id)
    save_subscriptions(subs)

def is_subscribed(user_id: int) -> bool:
    return user_id in load_subscriptions()
