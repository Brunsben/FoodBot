"""
Zentrale Konfiguration mit Validierung
Verhindert Fehler durch fehlende oder ungültige Umgebungsvariablen
"""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Lade .env Datei
load_dotenv()


@dataclass
class Config:
    """Zentrale App-Konfiguration mit Validierung"""
    
    # Core Settings
    SECRET_KEY: str
    DATABASE_URI: str = 'sqlite:///foodbot.db'
    
    # Session
    SESSION_LIFETIME_HOURS: int = 1
    SESSION_COOKIE_SECURE: bool = False  # Auf True bei HTTPS setzen
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    
    # CSRF
    CSRF_ENABLED: bool = True
    CSRF_TIME_LIMIT: int = 3600  # 1 Stunde
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_STORAGE: str = "memory://"
    
    # Performance
    SEND_FILE_MAX_AGE: int = 31536000  # 1 Jahr für statische Assets
    
    # Database Pooling
    DB_POOL_SIZE: int = 10
    DB_POOL_RECYCLE: int = 3600
    DB_MAX_OVERFLOW: int = 5
    
    @classmethod
    def from_env(cls) -> 'Config':
        """
        Erstellt Config-Objekt aus Umgebungsvariablen mit Validierung
        
        Raises:
            ValueError: Wenn SECRET_KEY fehlt oder ungültig ist
            
        Returns:
            Validiertes Config-Objekt
        """
        secret = os.getenv('SECRET_KEY')
        
        # Kritische Validierung: SECRET_KEY
        if not secret:
            raise ValueError(
                "❌ SECRET_KEY fehlt in .env Datei!\n"
                "Generiere einen mit: python3 -c 'import secrets; print(secrets.token_hex(32))'"
            )
        
        # Verbiete unsichere Default-Keys
        unsafe_keys = [
            'dev-secret-key-change-in-production',
            'change-me-in-production',
            'your-secret-key-here',
            'secret'
        ]
        if secret in unsafe_keys:
            raise ValueError(
                f"❌ SECRET_KEY '{secret}' ist unsicher!\n"
                "Generiere einen sicheren Key mit: python3 -c 'import secrets; print(secrets.token_hex(32))'"
            )
        
        # Minimale Länge prüfen
        if len(secret) < 32:
            raise ValueError(
                f"❌ SECRET_KEY zu kurz ({len(secret)} Zeichen, min 32)!\n"
                "Generiere einen längeren Key mit: python3 -c 'import secrets; print(secrets.token_hex(32))'"
            )
        
        # Optional: Database URI
        db_uri = os.getenv('DATABASE_URI', cls.DATABASE_URI)
        
        # Optional: Integer-Werte mit Defaults
        session_hours = int(os.getenv('SESSION_LIFETIME_HOURS', cls.SESSION_LIFETIME_HOURS))
        db_pool_size = int(os.getenv('DB_POOL_SIZE', cls.DB_POOL_SIZE))
        db_pool_recycle = int(os.getenv('DB_POOL_RECYCLE', cls.DB_POOL_RECYCLE))
        db_max_overflow = int(os.getenv('DB_MAX_OVERFLOW', cls.DB_MAX_OVERFLOW))
        
        # Optional: Boolean-Werte
        https_enabled = os.getenv('HTTPS_ENABLED', 'false').lower() in ('true', '1', 'yes')
        
        return cls(
            SECRET_KEY=secret,
            DATABASE_URI=db_uri,
            SESSION_LIFETIME_HOURS=session_hours,
            SESSION_COOKIE_SECURE=https_enabled,
            DB_POOL_SIZE=db_pool_size,
            DB_POOL_RECYCLE=db_pool_recycle,
            DB_MAX_OVERFLOW=db_max_overflow
        )
    
    def to_flask_config(self) -> dict:
        """
        Konvertiert Config zu Flask-kompatiblem Dictionary
        
        Returns:
            Dictionary mit Flask-Config-Keys
        """
        return {
            'SECRET_KEY': self.SECRET_KEY,
            'SQLALCHEMY_DATABASE_URI': self.DATABASE_URI,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_size': self.DB_POOL_SIZE,
                'pool_recycle': self.DB_POOL_RECYCLE,
                'pool_pre_ping': True,
                'max_overflow': self.DB_MAX_OVERFLOW,
                'pool_timeout': 30
            },
            'PERMANENT_SESSION_LIFETIME': self.SESSION_LIFETIME_HOURS * 3600,
            'SESSION_COOKIE_SECURE': self.SESSION_COOKIE_SECURE,
            'SESSION_COOKIE_HTTPONLY': self.SESSION_COOKIE_HTTPONLY,
            'SESSION_COOKIE_SAMESITE': self.SESSION_COOKIE_SAMESITE,
            'WTF_CSRF_ENABLED': self.CSRF_ENABLED,
            'WTF_CSRF_TIME_LIMIT': self.CSRF_TIME_LIMIT,
            'WTF_CSRF_SSL_STRICT': False,
            'WTF_CSRF_CHECK_DEFAULT': True,
            'SEND_FILE_MAX_AGE_DEFAULT': self.SEND_FILE_MAX_AGE
        }


def load_config() -> Config:
    """
    Lädt und validiert die Konfiguration
    
    Returns:
        Validiertes Config-Objekt
        
    Raises:
        ValueError: Bei fehlender/ungültiger Konfiguration
    """
    try:
        return Config.from_env()
    except ValueError as e:
        print(f"\n{'='*60}")
        print("KONFIGURATIONSFEHLER")
        print(f"{'='*60}")
        print(str(e))
        print(f"{'='*60}\n")
        raise
