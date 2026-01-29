from flask import Blueprint, render_template, send_file
from .models import db, User, Menu, Registration, Guest
from .auth import login_required
from datetime import date, timedelta
import csv
from io import StringIO, BytesIO

stats_bp = Blueprint('stats', __name__, url_prefix='/stats')

@stats_bp.route('/')
@login_required
def index():
    """Statistik-Übersicht - nur Tage mit Menü"""
    # Letzte 14 Tage mit Menü
    days = []
    
    # Hole alle Menü-Einträge der letzten 180 Tage (ca. 6 Monate)
    start_date = date.today() - timedelta(days=180)
    menus = Menu.query.filter(Menu.date >= start_date).order_by(Menu.date.desc()).limit(14).all()
    
    for menu_entry in menus:
        day = menu_entry.date
        regs = Registration.query.filter_by(date=day).count()
        guest_entry = Guest.query.filter_by(date=day).first()
        guests = guest_entry.count if guest_entry else 0
        
        days.append({
            'date': day,
            'registrations': regs,
            'guests': guests,
            'total': regs + guests,
            'menu': menu_entry.description
        })
    
    # Durchschnittliche Teilnehmer
    totals = [d['total'] for d in days if d['total'] > 0]
    avg = sum(totals) / len(totals) if totals else 0
    
    return render_template('stats.html', days=days, average=round(avg, 1))

@stats_bp.route('/export')
@login_required
def export_csv():
    """CSV-Export aller Tage mit Menü als CSV"""
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Datum', 'Kameraden', 'Gäste', 'Gesamt', 'Menü'])
    
    # Hole alle Menü-Einträge der letzten 365 Tage
    start_date = date.today() - timedelta(days=365)
    menus = Menu.query.filter(Menu.date >= start_date).order_by(Menu.date.desc()).all()
    
    for menu_entry in menus:
        day = menu_entry.date
        regs = Registration.query.filter_by(date=day).all()
        guest_entry = Guest.query.filter_by(date=day).first()
        guests = guest_entry.count if guest_entry else 0
        
        writer.writerow([
            day.isoformat(),
            len(regs),
            guests,
            len(regs) + guests,
            menu_entry.description
        ])
    
    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'essensanmeldungen_{date.today()}.csv'
    )
