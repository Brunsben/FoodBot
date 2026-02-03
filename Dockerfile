# Multi-stage build für kleinere Image-Größe
FROM python:3.11-slim as builder

# Build-Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Virtual Environment erstellen
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Requirements installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Production Stage
# ============================================
FROM python:3.11-slim

# Runtime-Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Nicht-Root User erstellen
RUN useradd -m -u 1000 foodbot

# Virtual Environment von Builder kopieren
COPY --from=builder /opt/venv /opt/venv

# Arbeitsverzeichnis
WORKDIR /app

# Python-Pfad setzen
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Application Code kopieren
COPY --chown=foodbot:foodbot app/ ./app/
COPY --chown=foodbot:foodbot templates/ ./templates/
COPY --chown=foodbot:foodbot backup_db.py clear_registrations.py ./

# Verzeichnisse für Daten erstellen
RUN mkdir -p /app/backups /app/logs && \
    chown -R foodbot:foodbot /app

# User wechseln
USER foodbot

# Port exposen
EXPOSE 5001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5001/api/status')" || exit 1

# Gunicorn starten
CMD ["gunicorn", "-c", "python:app.gunicorn_config", "app:create_app()"]
