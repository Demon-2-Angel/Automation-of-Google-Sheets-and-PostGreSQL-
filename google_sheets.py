import gspread
import logging
from oauth2client.service_account import ServiceAccountCredentials
from config import SCOPE, SHEET_ID

# Authenticate with Google Sheets API
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
client = gspread.authorize(creds)

SHEET_ID = "1eifb-ZhU_bjpdsX6anTDe4FuEOLyOjHIoFIK5QeueHg"
# Open the Google Sheet
sheet = client.open_by_key(SHEET_ID).sheet1

def read_sheet_data():
    """Reads all records from the Google Sheet and returns them as a list of dictionaries."""
    try:
        records = sheet.get_all_records()
        logging.info("Read data from Google Sheet successfully.")
        return records
    except Exception as e:
        logging.error(f"Error reading data from Google Sheet: {e}")
        return []

def write_to_sheet(data):
    """Writes data to the Google Sheet, overwriting existing content."""
    try:
        logging.info("Writing data to Google Sheet...")
        print(f"Writing this data to Google Sheet: {data}")
        sheet.clear()
        sheet.update("A1", data)
        logging.info("Data written to Google Sheet successfully.")
    except Exception as e:
        logging.error(f"Error writing data to Google Sheet: {e}")

