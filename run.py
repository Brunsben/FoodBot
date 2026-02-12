#!/usr/bin/env python3
"""
FoodBot - Development Server
Starte die App mit: python3 run.py
"""

import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Debug-Modus nur in Development
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=5001, debug=debug)
