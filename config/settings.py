from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    BOT_TOKEN: str
    GOSZAKUP_API_TOKEN: str | None
    ZAKUPSK_API_TOKEN: str | None
    KEYWORDS: list[str]
    ALLOWED_USERS: list[int]

    def __init__(self):
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.GOSZAKUP_API_TOKEN = os.getenv("GOSZAKUP_API_TOKEN")
        self.ZAKUPSK_API_TOKEN = os.getenv("ZAKUPSK_API_TOKEN")
        self.KEYWORDS = os.getenv("KEYWORDS", "").split(",")
        self.SENDER_EMAIL = os.getenv("sender_email")
        self.SENDER_PASSWORD = os.getenv("sender_password")

        self.ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS", "").split(",")))

def get_settings():
    return Settings()
