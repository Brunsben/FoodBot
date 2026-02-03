import serial
from app.models import db, User
import logging
import os

logger = logging.getLogger(__name__)

def read_rfid(port=None, baudrate=None):
    if port is None:
        port = os.environ.get('RFID_PORT', '/dev/ttyUSB0')
    if baudrate is None:
        baudrate = int(os.environ.get('RFID_BAUDRATE', '115200'))
    
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        try:
            while True:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    logger.info(f"RFID gelesen: {data}")
                    # Annahme: Die Kartennummer steht direkt in der Zeile
                    return data
        finally:
            ser.close()
    except serial.SerialException as e:
        logger.error(f"RFID-Leser nicht verfügbar auf {port}: {e}")
        raise

def find_user_by_card(card_id):
    return User.query.filter_by(card_id=card_id).first()
