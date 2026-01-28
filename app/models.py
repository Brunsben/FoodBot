from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    personal_number = db.Column(db.String(20), unique=True, nullable=False)
    card_id = db.Column(db.String(50), unique=True, nullable=True)  # Transpondernummer

class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, unique=True)
    description = db.Column(db.String(200), nullable=False)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=date.today)
    user = db.relationship('User', backref=db.backref('registrations', lazy=True))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='_user_date_uc'),)

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, unique=True)
    count = db.Column(db.Integer, default=0)
