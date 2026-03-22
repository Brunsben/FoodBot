"""
Gunicorn Konfiguration für Raspberry Pi und Docker
"""
import os

# Server
bind = "0.0.0.0:5001"
workers = 2
worker_class = "sync"
timeout = 30
keepalive = 2

# Logging - Docker: stdout/stderr, Raspberry Pi: Dateien
if os.path.exists("/.dockerenv") or os.path.exists("/app/logs"):
    # Docker-Umgebung: stdout/stderr für docker logs
    accesslog = "-"
    errorlog = "-"
else:
    # Raspberry Pi / lokale Installation
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    accesslog = os.path.join(base_dir, "logs", "access.log")
    errorlog = os.path.join(base_dir, "logs", "error.log")
loglevel = "info"

# Process
proc_name = "foodbot"
