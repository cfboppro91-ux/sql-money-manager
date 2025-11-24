import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "MoneyManagerAPI"
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

settings = Settings()
