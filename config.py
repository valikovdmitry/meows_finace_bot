from dotenv import load_dotenv
import os


load_dotenv()

# API токены
TOKEN = os.getenv("TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# Путь к Google API ключу
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "data", "creds.json")

# Путь к дамп файлу категорий
SHEETS_DUMP_FILE = os.path.join(BASE_DIR, "data", "sheets_dump.json")