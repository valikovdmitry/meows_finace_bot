from dotenv import load_dotenv
import os


load_dotenv()
token = os.getenv("TOKEN")
spreadsheets_id = os.getenv("SPREADSHEET_ID")
