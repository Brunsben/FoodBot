"""
Authentifizierung für den Admin-Bereich
"""
from functools import wraps
from flask import session, redirect, url_for, request, render_template_string
import os

# Admin-Passwort aus Environment oder Default
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'feuerwehr2026')

def check_auth(password):
    """Prüft ob das Passwort korrekt ist"""
    return password == ADMIN_PASSWORD

def login_required(f):
    """Decorator für geschützte Routen"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('main.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - FoodBot</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a0000 0%, #2d0a0a 25%, #450a0a 50%, #2d0a0a 75%, #1a0000 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .login-box {
            background: rgba(20,20,20,0.95);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(220,38,38,0.4), 0 0 100px rgba(220,38,38,0.2);
            padding: 50px 40px;
            border: 1px solid #7f1d1d;
            max-width: 400px;
            width: 100%;
        }
        h1 {
            color: #ef4444;
            margin-bottom: 30px;
            font-size: 2em;
            text-align: center;
            text-shadow: 0 0 20px rgba(220,38,38,0.6);
        }
        h1:before { content: '🔒 '; }
        form {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        input[type="password"] {
            font-size: 1.2em;
            padding: 15px 20px;
            border-radius: 10px;
            border: 2px solid #374151;
            background: rgba(0,0,0,0.5);
            color: #fff;
            font-family: inherit;
        }
        input[type="password"]:focus {
            outline: none;
            border-color: #dc2626;
            box-shadow: 0 0 0 3px rgba(220,38,38,0.2);
        }
        button {
            background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
            color: #fff;
            border: none;
            padding: 15px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: bold;
            transition: all 0.3s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(220,38,38,0.6);
        }
        .error {
            background: rgba(127,29,29,0.8);
            color: #fca5a5;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #dc2626;
            text-align: center;
        }
        .info {
            color: #9ca3af;
            text-align: center;
            font-size: 0.9em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>Admin Login</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post">
            <input type="password" name="password" placeholder="Passwort" autofocus required>
            <button type="submit">Anmelden</button>
        </form>
        <div class="info">
            Zugriff nur für Administratoren
        </div>
    </div>
</body>
</html>
"""
