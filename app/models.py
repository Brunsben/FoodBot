from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)  # Index für schnelle Suche
    personal_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    card_id = db.Column(db.String(50), unique=True, nullable=True, index=True)  # Index für RFID-Lookup

class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, unique=True, index=True)  # Index für Datumsabfragen
    description = db.Column(db.String(200), nullable=False)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    date = db.Column(db.Date, default=date.today, index=True)  # Index für Tagesabfragen
    user = db.relationship('User', backref=db.backref('registrations', lazy=True))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='_user_date_uc'),
        db.Index('idx_registration_date_user', 'date', 'user_id'),  # Composite Index
    )

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, unique=True, index=True)
    count = db.Column(db.Integer, default=0)

class AdminLog(db.Model):
    """Log für Admin-Aktionen"""
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.now(), index=True)
    admin_user = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    details = db.Column(db.Text, nullable=True)
    
    def save(self):
        db.session.add(self)
        db.session.commit()
