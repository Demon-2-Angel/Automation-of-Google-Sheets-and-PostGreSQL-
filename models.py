from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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
