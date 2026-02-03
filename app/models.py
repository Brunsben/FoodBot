from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)  # Index für schnelle Suche
    personal_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    card_id = db.Column(db.String(50), unique=True, nullable=True, index=True)  # Index für RFID-Lookup
    mobile_token = db.Column(db.String(64), unique=True, nullable=True, index=True)  # Für mobile Anmeldung
    
    @staticmethod
    def generate_token():
        """Generiert einen sicheren Token für mobile Anmeldung"""
        import secrets
        return secrets.token_urlsafe(32)

class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today, unique=True, index=True)  # Index für Datumsabfragen
    description = db.Column(db.String(200), nullable=False)
    # Neue Felder für Zwei-Menü-System
    zwei_menues_aktiv = db.Column(db.Boolean, default=False)
    menu1_name = db.Column(db.String(200), nullable=True)  # Erstes Menü
    menu2_name = db.Column(db.String(200), nullable=True)  # Zweites Menü
    
    @property
    def menu1(self):
        """Für Kompatibilität: menu1_name oder description"""
        return self.menu1_name or self.description
    
    @property
    def menu2(self):
        """Zweites Menü oder None"""
        return self.menu2_name if self.zwei_menues_aktiv else None

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    date = db.Column(db.Date, default=date.today, index=True)  # Index für Tagesabfragen
    menu_choice = db.Column(db.Integer, default=1)  # 1 oder 2 für Menüauswahl
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

class PresetMenu(db.Model):
    """Vordefinierte Menüs zur Auswahl"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    sort_order = db.Column(db.Integer, default=0)  # Für Sortierung
    
    @staticmethod
    def get_all_ordered():
        return PresetMenu.query.order_by(PresetMenu.sort_order, PresetMenu.name).all()
