
from datetime import datetime
from urllib.parse import quote_plus
import logging
import os
from datetime import datetime
from urllib.parse import quote_plus

import gspread
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from oauth2client.service_account import ServiceAccountCredentials

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure Logging
logging.basicConfig(level=logging.INFO)

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

# Configure the SQLAlchemy part of the app instance
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Create the SQLAlchemy db instance
db = SQLAlchemy(app)

# Define the database model


class SheetData(db.Model):
    __tablename__ = "sheet_data"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime)  # Represents the timestamp of the original data
    last_updated = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )  # Represents the last time this record was modified

    def __repr__(self):
        return f"<SheetData(id={self.id}, name='{self.name}', email='{self.email}', timestamp='{self.timestamp}')>"


# Initialize the database
with app.app_context():
    db.create_all()

# Google Sheets API Setup
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Authenticate with Google Sheets API
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Open the Google Sheet (replace with your actual sheet ID)
sheet = client.open_by_key("1eifb-ZhU_bjpdsX6anTDe4FuEOLyOjHIoFIK5QeueHg").sheet1


# Google Sheets Functions
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
        sheet.clear()
        sheet.update("A1", data)
        logging.info("Data written to Google Sheet successfully.")
    except Exception as e:
        logging.error(f"Error writing data to Google Sheet: {e}")


# app.py (continued)

from datetime import datetime

def sync_sheet_to_db():
    """
    Reads data from Google Sheets and updates the PostgreSQL database.
    Handles conflicts using Last Write Wins based on the timestamp.
    """
    with app.app_context():
        records = read_sheet_data()  # Fetch records from Google Sheets
        for record in records:
            try:
                # Extract data from Google Sheets
                record_id = int(record["ID"])
                name = record["Name"]
                email = record["Email"]
                timestamp_str = record["Timestamp"]
                sheet_timestamp = (
                    datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    if timestamp_str
                    else None
                )

                # Check if the record exists in the database
                existing_entry = SheetData.query.filter_by(id=record_id).first()

                if existing_entry:
                    # Compare timestamps to resolve conflicts (Last Write Wins)
                    if sheet_timestamp and sheet_timestamp > existing_entry.last_updated:
                        # Google Sheet has a more recent change, update the database
                        existing_entry.name = name
                        existing_entry.email = email
                        existing_entry.timestamp = sheet_timestamp
                        existing_entry.last_updated = (
                            datetime.utcnow()
                        )  # Update the last_updated timestamp
                else:
                    # The record doesn't exist in the database, insert it
                    new_entry = SheetData(
                        id=record_id,
                        name=name,
                        email=email,
                        timestamp=sheet_timestamp,
                        last_updated=datetime.utcnow(),  # Set the last_updated timestamp to now
                    )
                    db.session.add(new_entry)

            except Exception as e:
                print(f"Error processing record {record}: {e}")

        # Commit changes to the database
        db.session.commit()


def sync_db_to_sheet():
    """
    Fetches data from the PostgreSQL database and writes it to Google Sheets.
    Handles conflicts using Last Write Wins based on the timestamp.
    """
    with app.app_context():
        try:
            records = SheetData.query.all()  # Fetch all records from the database
            sheet_records = read_sheet_data()  # Fetch all records from Google Sheets
            sheet_data = {
                int(row["ID"]): row for row in sheet_records
            }  # Convert sheet data to dictionary for easy lookup

            # Prepare data for Google Sheets update
            data = [["ID", "Name", "Email", "Timestamp"]]  # Header row

            for record in records:
                sheet_record = sheet_data.get(record.id)
                if sheet_record:
                    # Compare timestamps to resolve conflicts (Last Write Wins)
                    sheet_timestamp_str = sheet_record["Timestamp"]
                    sheet_timestamp = (
                        datetime.strptime(sheet_timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if sheet_timestamp_str
                        else None
                    )

                    if record.last_updated > sheet_timestamp:
                        # Database has a more recent change, update Google Sheets
                        data.append(
                            [
                                record.id,
                                record.name,
                                record.email,
                                record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            ]
                        )
                    else:
                        # Keep the Google Sheet version as it's more recent
                        data.append(
                            [
                                sheet_record["ID"],
                                sheet_record["Name"],
                                sheet_record["Email"],
                                sheet_record["Timestamp"],
                            ]
                        )
                else:
                    # Record doesn't exist in the Google Sheet, insert it
                    data.append(
                        [
                            record.id,
                            record.name,
                            record.email,
                            record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        ]
                    )

            # Write the data back to the Google Sheet
            write_to_sheet(data)

        except Exception as e:
            print(f"Error syncing data to sheet: {e}")

# Flask Routes
@app.route("/")
def home():
    """Endpoint for the root URL."""
    return "Welcome to the Flask App!"


@app.route("/favicon.ico")
def favicon():
    """Serves the favicon.ico file."""
    return send_from_directory(os.path.join(app.root_path, "static"), "favicon.ico")


@app.route("/read_sheet")
def read_sheet():
    """Endpoint to read data from the Google Sheet."""
    data = read_sheet_data()
    return jsonify({"data": data}), 200


@app.route("/write_sheet")
def write_sheet():
    """Endpoint to write sample data to the Google Sheet."""
    # Example data to write
    data = [["ID", "Name", "Email", "Timestamp"]]
    write_to_sheet(data)
    return "Data written to sheet successfully.", 200


@app.route("/sync_sheet_to_db")
def sync_sheet_to_db_route():
    sync_sheet_to_db()
    return "Sheet data synchronized to database successfully."


@app.route("/sync_db_to_sheet")
def sync_db_to_sheet_route():
    sync_db_to_sheet()
    return "Database data synchronized to sheet successfully."

# CRUD Operations
@app.route("/create", methods=["POST"])
def create_record():
    """
    Endpoint to create a new record in the database.
    Expects JSON input with 'name', 'email', and 'timestamp' fields.
    """
    data = request.get_json()

    if not data or 'name' not in data or 'email' not in data or 'timestamp' not in data:
        return jsonify({"error": "Invalid input"}), 400

    try:
        # Convert timestamp string to datetime object
        timestamp = datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S")

        # Create a new SheetData record, without manually specifying the 'id'
        new_record = SheetData(
            name=data['name'],
            email=data['email'],
            timestamp=timestamp,
            last_updated=datetime.utcnow()
        )

        db.session.add(new_record)
        db.session.commit()

        return jsonify({"message": "Record created successfully"}), 201
    except Exception as e:
        logging.error(f"Error creating record: {e}")
        return jsonify({"error": "Failed to create record"}), 500



@app.route("/records", methods=["GET"])
def get_records():
    """
    Endpoint to fetch all records from the database.
    """
    try:
        records = SheetData.query.all()
        result = [
            {
                "id": record.id,
                "name": record.name,
                "email": record.email,
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "last_updated": record.last_updated.strftime("%Y-%m-%d %H:%M:%S")
            }
            for record in records
        ]
        return jsonify({"records": result}), 200
    except Exception as e:
        logging.error(f"Error fetching records: {e}")
        return jsonify({"error": "Failed to fetch records"}), 500


@app.route("/records/<int:id>", methods=["GET"])
def get_record(id):
    """
    Endpoint to fetch a specific record by its ID.
    """
    try:
        record = SheetData.query.get_or_404(id)
        result = {
            "id": record.id,
            "name": record.name,
            "email": record.email,
            "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": record.last_updated.strftime("%Y-%m-%d %H:%M:%S")
        }
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error fetching record: {e}")
        return jsonify({"error": "Failed to fetch record"}), 500

@app.route("/update/<int:id>", methods=["PUT"])
def update_record(id):
    """
    Endpoint to update an existing record by its ID.
    Expects JSON input with 'name', 'email', and 'timestamp' fields.
    """
    data = request.get_json()

    if not data or 'name' not in data or 'email' not in data or 'timestamp' not in data:
        return jsonify({"error": "Invalid input"}), 400

    try:
        record = SheetData.query.get_or_404(id)
        
        # Update the record fields
        record.name = data['name']
        record.email = data['email']
        record.timestamp = datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S")
        record.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({"message": "Record updated successfully"}), 200
    except Exception as e:
        logging.error(f"Error updating record: {e}")
        return jsonify({"error": "Failed to update record"}), 500

@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_record(id):
    """
    Endpoint to delete a specific record by its ID.
    """
    try:
        record = SheetData.query.get_or_404(id)
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({"message": "Record deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting record: {e}")
        return jsonify({"error": "Failed to delete record"}), 500


import atexit

from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# Sync Google Sheets to DB every 5 minutes
scheduler.add_job(func=sync_sheet_to_db, trigger="interval", minutes=5)

# Sync DB to Google Sheets every 5 minutes
scheduler.add_job(func=sync_db_to_sheet, trigger="interval", minutes=5)

scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
