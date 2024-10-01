from flask import current_app
from models import SheetData, db
from google_sheets import read_sheet_data, write_to_sheet
from datetime import datetime


def sync_sheet_to_db():
    """Sync data from Google Sheets to the PostgreSQL database."""
    # Push the application context
    with current_app.app_context():
        try:
            # Fetch records from Google Sheets
            records = read_sheet_data()
            print("Fetched records from Google Sheets:")
            for record in records:
                print(f"Record: {record}")

            for record in records:
                try:
                    record_id = int(record["ID"])
                    name = record["Name"]
                    email = record["Email"]
                    timestamp_str = record["Timestamp"]
                    sheet_timestamp = (
                        datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if timestamp_str
                        else None
                    )

                    # Print record details for debugging
                    print(f"Processing record with ID: {record_id}, Name: {name}, Email: {email}, Timestamp: {sheet_timestamp}")

                    # Check if the record exists in the database
                    existing_entry = SheetData.query.filter_by(id=record_id).first()

                    if existing_entry:
                        # Compare timestamps to resolve conflicts (Last Write Wins)
                        print(f"Existing entry found: {existing_entry}")
                        if sheet_timestamp and sheet_timestamp > existing_entry.last_updated:
                            # Google Sheet has a more recent change, update the database
                            print(f"Updating entry with ID {record_id} in the database.")
                            existing_entry.name = name
                            existing_entry.email = email
                            existing_entry.timestamp = sheet_timestamp
                            existing_entry.last_updated = datetime.utcnow()
                    else:
                        # The record doesn't exist in the database, insert it
                        print(f"Inserting new entry with ID {record_id} into the database.")
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
            print("Committing changes to the database.")
            db.session.commit()

        except Exception as e:
            print(f"Error fetching data from Google Sheets or processing records: {e}")

def sync_db_to_sheet():
    """Sync data from PostgreSQL to Google Sheets."""
    # Push the application context
    with current_app.app_context():
        try:
            # Fetch all records from the database
            records = SheetData.query.all()
            print("Fetched records from DB:")
            for record in records:
                print(f"Record ID: {record.id}, Name: {record.name}")
            
            # Fetch all records from Google Sheets
            sheet_records = read_sheet_data()
            sheet_data = {int(row["ID"]): row for row in sheet_records}
            print(f"Google Sheets data IDs: {sheet_data.keys()}")

            # Prepare data for Google Sheets update
            data = [["ID", "Name", "Email", "Timestamp"]]  # Header row

            for record in records:
                sheet_record = sheet_data.get(record.id)
                if sheet_record:
                    sheet_timestamp_str = sheet_record["Timestamp"]
                    sheet_timestamp = (
                        datetime.strptime(sheet_timestamp_str, "%Y-%m-%d %H:%M:%S")
                        if sheet_timestamp_str
                        else None
                    )
                    print(f"Comparing DB last_updated: {record.last_updated} with Sheet timestamp: {sheet_timestamp}")

                    if record.last_updated > sheet_timestamp:
                        # DB has more recent data, update Google Sheets
                        data.append(
                            [
                                record.id,
                                record.name,
                                record.email,
                                record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            ]
                        )
                    else:
                        # Google Sheets data is more recent or same, keep it
                        data.append(
                            [
                                sheet_record["ID"],
                                sheet_record["Name"],
                                sheet_record["Email"],
                                sheet_record["Timestamp"],
                            ]
                        )
                else:
                    # Record doesn't exist in Google Sheets, insert it
                    data.append(
                        [
                            record.id,
                            record.name,
                            record.email,
                            record.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        ]
                    )

            # Debugging: Print final data that will be written to Google Sheets
            print("Data prepared for Google Sheets:")
            for row in data:
                print(row)

            # Write the data back to the Google Sheet
            write_to_sheet(data)

        except Exception as e:
            print(f"Error syncing data to sheet: {e}")