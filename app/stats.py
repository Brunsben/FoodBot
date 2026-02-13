from flask import Blueprint, render_template, send_file
from .models import db, User, Menu, Registration, Guest
from .auth import login_required
from datetime import date, timedelta
from sqlalchemy import func
import csv
from io import StringIO, BytesIO

stats_bp = Blueprint('stats', __name__, url_prefix='/stats')


def _build_stats_for_menus(menus):
    """Baut Statistik-Daten für eine Liste von Menüs effizient auf."""
    if not menus:
        return []
    
    dates = [m.date for m in menus]
    
    # Alle Registrierungen für diese Tage in einer Query
    reg_data = db.session.query(
        Registration.date,
        Registration.menu_choice,
        func.count(Registration.id)
    ).filter(Registration.date.in_(dates)
    ).group_by(Registration.date, Registration.menu_choice).all()
    
    # Alle Gäste für diese Tage in einer Query
    guest_data = Guest.query.filter(Guest.date.in_(dates)).all()
    
    # Lookup-Dicts aufbauen
    reg_counts = {}  # {date: {menu_choice: count}}
    for reg_date, menu_choice, count in reg_data:
        if reg_date not in reg_counts:
            reg_counts[reg_date] = {}
        reg_counts[reg_date][menu_choice] = count
    
    guest_counts = {g.date: g.count for g in guest_data}
    
    days = []
    for menu_entry in menus:
        day = menu_entry.date
        day_regs = reg_counts.get(day, {})
        total_regs = sum(day_regs.values())
        guests = guest_counts.get(day, 0)
        
        entry = {
            'date': day,
            'registrations': total_regs,
            'guests': guests,
            'total': total_regs + guests,
            'menu': menu_entry.description,
        }
        
        if menu_entry.zwei_menues_aktiv:
            entry['zwei_menues'] = True
            entry['menu1_name'] = menu_entry.menu1_name
            entry['menu2_name'] = menu_entry.menu2_name
            entry['menu1_count'] = day_regs.get(1, 0)
            entry['menu2_count'] = day_regs.get(2, 0)
        else:
            entry['zwei_menues'] = False
        
        days.append(entry)
    
    return days


@stats_bp.route('/')
@login_required
def index():
    """Statistik-Übersicht - nur Tage mit Menü"""
    start_date = date.today() - timedelta(days=180)
    menus = Menu.query.filter(Menu.date >= start_date).order_by(Menu.date.desc()).limit(14).all()
    
    days = _build_stats_for_menus(menus)
    
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
    
    start_date = date.today() - timedelta(days=365)
    menus = Menu.query.filter(Menu.date >= start_date).order_by(Menu.date.desc()).all()
    
    days = _build_stats_for_menus(menus)
    
    for d in days:
        if d.get('zwei_menues'):
            writer.writerow([
                d['date'].isoformat(),
                d['registrations'],
                d['guests'],
                d['total'],
                d['menu'],
                'Ja',
                d.get('menu1_name', ''),
                d.get('menu1_count', 0),
                d.get('menu2_name', ''),
                d.get('menu2_count', 0)
            ])
        else:
            writer.writerow([
                d['date'].isoformat(),
                d['registrations'],
                d['guests'],
                d['total'],
                d['menu'],
                'Nein', '', '', '', ''
            ])
    
    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'essensanmeldungen_{date.today()}.csv'
    )
