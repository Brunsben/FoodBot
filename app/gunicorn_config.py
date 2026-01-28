"""
Gunicorn Konfiguration für Docker Container
"""

import multiprocessing

# Server
bind = "0.0.0.0:5001"
workers = 2  # Für Raspberry Pi - nicht zu viele Workers
worker_class = "sync"
timeout = 30
keepalive = 2

# Logging
accesslog = "/app/logs/access.log"
errorlog = "/app/logs/error.log"
loglevel = "info"

# Process
proc_name = "foodbot"
