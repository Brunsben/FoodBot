from app import create_app
from app.models import db, Registration
from datetime import date

app = create_app()

with app.app_context():
    deleted = Registration.query.delete()
    db.session.commit()
    print(f"{deleted} Anmeldungen gelöscht.")
