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
        all_regs = Registration.query.filter_by(date=day).all()
        guest_entry = Guest.query.filter_by(date=day).first()
        guests = guest_entry.count if guest_entry else 0
        
        # Prüfe ob zwei Menüs aktiv waren
        if menu_entry.zwei_menues_aktiv:
            menu1_regs = sum(1 for r in all_regs if r.menu_choice == 1)
            menu2_regs = sum(1 for r in all_regs if r.menu_choice == 2)
            
            days.append({
                'date': day,
                'registrations': len(all_regs),
                'guests': guests,
                'total': len(all_regs) + guests,
                'menu': menu_entry.description,
                'zwei_menues': True,
                'menu1_name': menu_entry.menu1_name,
                'menu2_name': menu_entry.menu2_name,
                'menu1_count': menu1_regs,
                'menu2_count': menu2_regs
            })
        else:
            days.append({
                'date': day,
                'registrations': len(all_regs),
                'guests': guests,
                'total': len(all_regs) + guests,
                'menu': menu_entry.description,
                'zwei_menues': False
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
    writer.writerow(['Datum', 'Kameraden', 'Gäste', 'Gesamt', 'Menü', 'Zwei Menüs', 'Menü 1', 'Menü 1 Anzahl', 'Menü 2', 'Menü 2 Anzahl'])
    
    # Hole alle Menü-Einträge der letzten 365 Tage
    start_date = date.today() - timedelta(days=365)
    menus = Menu.query.filter(Menu.date >= start_date).order_by(Menu.date.desc()).all()
    
    for menu_entry in menus:
        day = menu_entry.date
        all_regs = Registration.query.filter_by(date=day).all()
        guest_entry = Guest.query.filter_by(date=day).first()
        guests = guest_entry.count if guest_entry else 0
        
        if menu_entry.zwei_menues_aktiv:
            menu1_regs = sum(1 for r in all_regs if r.menu_choice == 1)
            menu2_regs = sum(1 for r in all_regs if r.menu_choice == 2)
            
            writer.writerow([
                day.isoformat(),
                len(all_regs),
                guests,
                len(all_regs) + guests,
                menu_entry.description,
                'Ja',
                menu_entry.menu1_name,
                menu1_regs,
                menu_entry.menu2_name,
                menu2_regs
            ])
        else:
            writer.writerow([
                day.isoformat(),
                len(all_regs),
                guests,
                len(all_regs) + guests,
                menu_entry.description,
                'Nein',
                '',
                '',
                '',
                ''
            ])
    
    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'essensanmeldungen_{date.today()}.csv'
    )
