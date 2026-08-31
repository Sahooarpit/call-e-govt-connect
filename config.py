import os
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./city_incidents.db")
    CALLE_API_KEY = os.getenv("CALLE_API_KEY")
    CALLE_PHONE_NUMBER = os.getenv("CALLE_PHONE_NUMBER")

settings = Settings()
