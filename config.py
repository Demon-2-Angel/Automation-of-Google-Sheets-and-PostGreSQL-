import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# Retrieve database credentials from environment variables
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_NAME = os.getenv("DB_NAME")

# URL-encode the password
DB_PASSWORD_ENCODED = quote_plus(DB_PASSWORD)

# Construct the database URI
DATABASE_URI = f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD_ENCODED}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Google Sheets API Setup
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SHEET_ID = "1eifb-ZhU_bjpdsX6anTDe4FuEOLyOjHIoFIK5QeueHg"
