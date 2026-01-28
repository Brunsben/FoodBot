"""
Essenshistorie - Pro-User-Statistiken
"""
from flask import Blueprint, render_template
from .models import db, User, Registration
from .auth import login_required
from datetime import date, timedelta
from sqlalchemy import func

history_bp = Blueprint('history', __name__, url_prefix='/history')

@history_bp.route('/')
@login_required
def index():
    """Essenshistorie aller User"""
    # Zeitraum: Letzte 90 Tage
    start_date = date.today() - timedelta(days=90)
    
    # User mit Statistiken
    users = User.query.order_by(User.name).all()
    user_stats = []
    
    for user in users:
        # Anzahl Anmeldungen in den letzten 90 Tagen
        count_90 = Registration.query.filter(
            Registration.user_id == user.id,
            Registration.date >= start_date
        ).count()
        
        # Anzahl Anmeldungen in den letzten 30 Tagen
        count_30 = Registration.query.filter(
            Registration.user_id == user.id,
            Registration.date >= date.today() - timedelta(days=30)
        ).count()
        
        # Anzahl Anmeldungen in den letzten 7 Tagen
        count_7 = Registration.query.filter(
            Registration.user_id == user.id,
            Registration.date >= date.today() - timedelta(days=7)
        ).count()
        
        # Letzte Anmeldung
        last_reg = Registration.query.filter(
            Registration.user_id == user.id
        ).order_by(Registration.date.desc()).first()
        
        user_stats.append({
            'user': user,
            'count_90': count_90,
            'count_30': count_30,
            'count_7': count_7,
            'last_date': last_reg.date if last_reg else None
        })
    
    # Top 10 Esser (90 Tage)
    top_users = sorted(user_stats, key=lambda x: x['count_90'], reverse=True)[:10]
    
    return render_template('history.html', 
                         user_stats=user_stats, 
                         top_users=top_users,
                         total_users=len(users))

@history_bp.route('/user/<int:user_id>')
@login_required
def user_detail(user_id):
    """Detail-Ansicht für einen User"""
    user = User.query.get_or_404(user_id)
    
    # Alle Anmeldungen des Users (letzte 180 Tage)
    start_date = date.today() - timedelta(days=180)
    registrations = Registration.query.filter(
        Registration.user_id == user_id,
        Registration.date >= start_date
    ).order_by(Registration.date.desc()).all()
    
    # Gruppiere nach Monat
    from collections import defaultdict
    by_month = defaultdict(int)
    for reg in registrations:
        month_key = reg.date.strftime('%Y-%m')
        by_month[month_key] += 1
    
    return render_template('history_detail.html',
                         user=user,
                         registrations=registrations,
                         by_month=sorted(by_month.items(), reverse=True),
                         total=len(registrations))
