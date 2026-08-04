import os


class Settings:
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_URL: str = os.getenv("DB_URL", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))
    PIN_MAX_ATTEMPTS: int = 5
    PIN_LOCKOUT_MINUTES: int = 5
    CORS_ORIGINS: list[str] = ["*"]

    def __init__(self):
        if not self.DB_URL:
            self.DB_URL = f"sqlite:///{os.path.join(self.BASE_DIR, 'data.db')}"


settings = Settings()
