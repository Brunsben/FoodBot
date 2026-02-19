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
    today = date.today()
    start_90 = today - timedelta(days=90)
    start_30 = today - timedelta(days=30)
    start_7 = today - timedelta(days=7)
    
    # Aggregierte Query statt N+1 (eine Query statt 4 pro User)
    from sqlalchemy import case
    
    stats_query = db.session.query(
        User.id,
        User.name,
        User.personal_number,
        func.count(case((Registration.date >= start_90, 1))).label('count_90'),
        func.count(case((Registration.date >= start_30, 1))).label('count_30'),
        func.count(case((Registration.date >= start_7, 1))).label('count_7'),
        func.max(Registration.date).label('last_date')
    ).outerjoin(
        Registration, 
        (User.id == Registration.user_id) & (Registration.date >= start_90)
    ).group_by(User.id, User.name, User.personal_number)\
     .order_by(User.name).all()
    
    user_stats = []
    for row in stats_query:
        user_stats.append({
            'user': type('User', (), {'id': row.id, 'name': row.name, 'personal_number': row.personal_number})(),
            'count_90': row.count_90,
            'count_30': row.count_30,
            'count_7': row.count_7,
            'last_date': row.last_date
        })
    
    # Top 10 Esser (90 Tage)
    top_users = sorted(user_stats, key=lambda x: x['count_90'], reverse=True)[:10]
    
    return render_template('history.html', 
                         user_stats=user_stats, 
                         top_users=top_users,
                         total_users=len(user_stats))

@history_bp.route('/user/<int:user_id>')
@login_required
def user_detail(user_id):
    """Detail-Ansicht für einen User mit Pagination"""
    from flask import request
    user = db.session.get(User, user_id)
    if not user:
        from flask import abort
        abort(404)
    
    # Pagination-Parameter
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 100)  # Max 100 Einträge pro Seite
    
    # Alle Anmeldungen des Users (letzte 180 Tage) mit Pagination
    start_date = date.today() - timedelta(days=180)
    pagination = Registration.query.filter(
        Registration.user_id == user_id,
        Registration.date >= start_date
    ).order_by(Registration.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Gruppiere nach Monat (nur angezeigte Registrierungen)
    from collections import defaultdict
    by_month = defaultdict(int)
    for reg in pagination.items:
        month_key = reg.date.strftime('%Y-%m')
        by_month[month_key] += 1
    
    return render_template('history_detail.html',
                         user=user,
                         registrations=pagination.items,
                         pagination=pagination,
                         by_month=dict(sorted(by_month.items(), reverse=True)))
                         registrations=registrations,
                         by_month=sorted(by_month.items(), reverse=True),
                         total=len(registrations))
