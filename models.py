"""
Database Models for Medication Tracking System
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())

    medications = db.relationship('Medication', backref='user', lazy=True, cascade='all, delete-orphan')
    measurements = db.relationship('Measurement', backref='user', lazy=True, cascade='all, delete-orphan')
    taken_medications = db.relationship('TakenMedication', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Medication(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    time = db.Column(db.Time, nullable=False)
    period = db.Column(db.String(20), default='daily')
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    last_taken = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'dosage': self.dosage,
            'time': self.time.isoformat() if self.time else None,
            'period': self.period,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_taken': self.last_taken.isoformat() if self.last_taken else None
        }

class TakenMedication(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    medication_id = db.Column(db.String(36), db.ForeignKey('medication.id'), nullable=False)
    taken_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    date = db.Column(db.Date, default=lambda: datetime.utcnow().date())

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'medication_id': self.medication_id,
            'taken_at': self.taken_at.isoformat(),
            'date': str(self.date)
        }

class Measurement(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    systolic = db.Column(db.Integer)
    diastolic = db.Column(db.Integer)
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), nullable=False)
    notes = db.Column(db.Text)
    measured_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())

    def to_dict(self):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'value': self.value,
            'unit': self.unit,
            'notes': self.notes,
            'measured_at': self.measured_at.isoformat()
        }
        if self.type == 'blood_pressure':
            data.update({
                'systolic': self.systolic,
                'diastolic': self.diastolic
            })
        return data
