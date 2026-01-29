"""
Gunicorn Konfiguration für FoodBot Production Deployment
=========================================================

Führe aus mit: gunicorn -c deployment/gunicorn.conf.py "app:create_app()"
"""

import multiprocessing
import os

# Server Socket
bind = "0.0.0.0:5001"
backlog = 2048

# Worker Prozesse
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "foodbot"

# Server mechanics
daemon = False
pidfile = None  # Kein pidfile nötig bei systemd
umask = 0
user = None  # Run as current user (oder setze auf 'www-data' für Nginx)
group = None
tmp_upload_dir = None

# SSL (optional, falls direkt ohne Nginx)
# keyfile = "/path/to/key.pem"
# certfile = "/path/to/cert.pem"

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    """Called just prior to forking."""
    pass

def pre_exec(server):
    """Called just prior to forking off a new master process."""
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("worker received SIGABRT signal")
