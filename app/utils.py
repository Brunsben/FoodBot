from .models import db, User, Registration
from datetime import date

def register_user_for_today(user: User):
    existing = Registration.query.filter_by(user_id=user.id, date=date.today()).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return False  # Abgemeldet
    else:
        reg = Registration(user_id=user.id, date=date.today())
        db.session.add(reg)
        db.session.commit()
        return True  # Angemeldet
