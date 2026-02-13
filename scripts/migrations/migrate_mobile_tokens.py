#!/usr/bin/env python3
"""
Migrationsskript für mobile Tokens
Fügt mobile_token Spalte hinzu und generiert Tokens für alle User
"""
from app import create_app
from app.models import db, User
from sqlalchemy import text
import sys

def migrate_database():
    app = create_app()
    
    with app.app_context():
        print("🔄 Starte Datenbank-Migration für mobile Tokens...")
        
        try:
            # Prüfe ob Spalte schon existiert
            inspector = db.inspect(db.engine)
            user_columns = [col['name'] for col in inspector.get_columns('user')]
            
            if 'mobile_token' not in user_columns:
                print("  ➕ Füge 'mobile_token' zu User hinzu...")
                db.session.execute(text('ALTER TABLE user ADD COLUMN mobile_token VARCHAR(64)'))
                db.session.commit()
            else:
                print("  ✓ 'mobile_token' existiert bereits")
            
            # Generiere Tokens für alle User ohne Token
            users_without_token = User.query.filter_by(mobile_token=None).all()
            if users_without_token:
                print(f"  🔑 Generiere Tokens für {len(users_without_token)} User...")
                for user in users_without_token:
                    user.mobile_token = User.generate_token()
                db.session.commit()
                print(f"  ✅ {len(users_without_token)} Tokens generiert")
            else:
                print("  ✓ Alle User haben bereits Tokens")
            
            print("✅ Migration erfolgreich abgeschlossen!")
            return True
            
        except Exception as e:
            print(f"❌ Fehler bei der Migration: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = migrate_database()
    sys.exit(0 if success else 1)
