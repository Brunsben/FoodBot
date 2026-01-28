#!/usr/bin/env python3
"""
Benachrichtigungs-Service für FoodBot
Sendet Benachrichtigungen bei wichtigen Events (z.B. neue Anmeldung, wenig Teilnehmer)
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """Basis-Klasse für Benachrichtigungen"""
    
    def __init__(self):
        self.enabled = os.environ.get('NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
        self.webhook_url = os.environ.get('WEBHOOK_URL')
    
    def send_notification(self, message, level='info'):
        """Sende Benachrichtigung (Webhook, E-Mail, etc.)"""
        if not self.enabled:
            return
        
        timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        log_message = f"[{timestamp}] {level.upper()}: {message}"
        
        # Console-Ausgabe
        logger.info(log_message)
        
        # Webhook (z.B. für Slack, Discord, etc.)
        if self.webhook_url:
            try:
                import requests
                payload = {'text': log_message}
                requests.post(self.webhook_url, json=payload, timeout=5)
            except Exception as e:
                logger.error(f"Webhook-Fehler: {e}")
    
    def notify_new_registration(self, user_name):
        """Benachrichtigung bei neuer Anmeldung"""
        self.send_notification(f"✅ {user_name} hat sich zum Essen angemeldet")
    
    def notify_low_attendance(self, count, threshold=5):
        """Benachrichtigung bei wenig Anmeldungen"""
        if count < threshold:
            self.send_notification(f"⚠️ Nur {count} Anmeldungen für heute", level='warning')
    
    def notify_high_attendance(self, count):
        """Benachrichtigung bei vielen Anmeldungen"""
        if count > 30:
            self.send_notification(f"🔥 Hohe Teilnehmerzahl: {count} Anmeldungen!", level='info')

# Globale Instanz
notification_service = NotificationService()
