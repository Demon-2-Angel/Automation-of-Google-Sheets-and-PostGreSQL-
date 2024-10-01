from flask import jsonify, request
from models import SheetData, db
from datetime import datetime

def create_record():
    data = request.get_json()
    if not data or 'name' not in data or 'email' not in data or 'timestamp' not in data:
        return jsonify({"error": "Invalid input"}), 400
    try:
        timestamp = datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S")
        new_record = SheetData(name=data['name'], email=data['email'], timestamp=timestamp, last_updated=datetime.utcnow())
        db.session.add(new_record)
        db.session.commit()
        return jsonify({"message": "Record created successfully"}), 201
    except Exception as e:
        return jsonify({"error": "Failed to create record"}), 500

def get_records():
    try:
        records = SheetData.query.all()
        result = [
            {"id": record.id, "name": record.name, "email": record.email, "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "last_updated": record.last_updated.strftime("%Y-%m-%d %H:%M:%S")}
            for record in records
        ]
        return jsonify({"records": result}), 200
    except Exception as e:
        return jsonify({"error": "Failed to fetch records"}), 500

def get_record(id):
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
        return jsonify({"error": "Failed to fetch record"}), 500

def update_record(id):
    data = request.get_json()
    if not data or 'name' not in data or 'email' not in data or 'timestamp' not in data:
        return jsonify({"error": "Invalid input"}), 400

    try:
        record = SheetData.query.get_or_404(id)
        record.name = data['name']
        record.email = data['email']
        record.timestamp = datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S")
        record.last_updated = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Record updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to update record"}), 500

def delete_record(id):
    try:
        record = SheetData.query.get_or_404(id)
        db.session.delete(record)
        db.session.commit()
        return jsonify({"message": "Record deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to delete record"}), 500
