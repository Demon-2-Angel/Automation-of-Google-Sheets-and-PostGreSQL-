import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define the scope
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Authenticate using the service account
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

# Open the Google Sheet
# Open the Google Sheet
sheet = client.open_by_key('1eifb-ZhU_bjpdsX6anTDe4FuEOLyOjHIoFIK5QeueHg').sheet1

# Test writing some simple data
test_data = [
    ['ID', 'Name', 'Email'],
    [1, 'John Doe', 'john@example.com'],    
    [2, 'Jane Doe', 'jane@example.com']
]

try:
    sheet.clear()  # Clear existing data
    sheet.update('A1', test_data)  # Write new data
    print("Data written successfully.")
except Exception as e:
    print(f"Error: {e}")
