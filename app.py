from flask import Flask
from config import DATABASE_URI
from models import db
from google_sheets import read_sheet_data, write_to_sheet
from sync import sync_sheet_to_db, sync_db_to_sheet
from crud import create_record, get_records, get_record, update_record, delete_record
from scheduler import scheduler

app = Flask(__name__)

# Configure the SQLAlchemy part of the app instance
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db.init_app(app)

with app.app_context():
    db.create_all()

# Flask Routes
@app.route("/")
def home():
    return "Welcome to the Flask App!"

@app.route("/create", methods=["POST"])
def create_record_route():
    return create_record()

@app.route("/records", methods=["GET"])
def get_records_route():
    return get_records()

@app.route("/records/<int:id>", methods=["GET"])
def get_record_route(id):
    return get_record(id)

@app.route("/update/<int:id>", methods=["PUT"])
def update_record_route(id):
    return update_record(id)

@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_record_route(id):
    return delete_record(id)

@app.route("/sync_sheet_to_db")
def sync_sheet_to_db_route():
    sync_sheet_to_db()
    return "Sheet data synchronized to database successfully."

@app.route("/sync_db_to_sheet")
def sync_db_to_sheet_route():
    sync_db_to_sheet()
    return "Database data synchronized to sheet successfully."

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
