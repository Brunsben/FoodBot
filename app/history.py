"""
Essenshistorie - Pro-Mitglied-Statistiken
"""
from flask import Blueprint, render_template
from .models import db, Registration, get_member_name, get_member, get_all_members
from .auth import login_required
from datetime import date, timedelta
from sqlalchemy import func

history_bp = Blueprint('history', __name__, url_prefix='/history')

@history_bp.route('/')
@login_required
def index():
    """Essenshistorie aller Mitglieder"""
    today = date.today()
    start_90 = today - timedelta(days=90)
    start_30 = today - timedelta(days=30)
    start_7 = today - timedelta(days=7)
    
    from sqlalchemy import case
    
    # Aggregierte Query über Registrierungen (member_id basiert)
    stats_query = db.session.query(
        Registration.member_id,
        func.count(case((Registration.datum >= start_90, 1))).label('count_90'),
        func.count(case((Registration.datum >= start_30, 1))).label('count_30'),
        func.count(case((Registration.datum >= start_7, 1))).label('count_7'),
        func.max(Registration.datum).label('last_date')
    ).filter(
        Registration.datum >= start_90
    ).group_by(Registration.member_id).all()
    
    # Stats-Dict aufbauen
    reg_stats = {}
    for row in stats_query:
        reg_stats[str(row.member_id)] = {
            'count_90': row.count_90,
            'count_30': row.count_30,
            'count_7': row.count_7,
            'last_date': row.last_date
        }
    
    # Alle Mitglieder laden
    members = get_all_members()
    
    user_stats = []
    for m in members:
        mid = m['id']
        s = reg_stats.get(mid, {'count_90': 0, 'count_30': 0, 'count_7': 0, 'last_date': None})
        user_stats.append({
            'member': m,
            'count_90': s['count_90'],
            'count_30': s['count_30'],
            'count_7': s['count_7'],
            'last_date': s['last_date']
        })
    
    # Top 10 Esser (90 Tage)
    top_users = sorted(user_stats, key=lambda x: x['count_90'], reverse=True)[:10]
    
    return render_template('history.html', 
                         user_stats=user_stats, 
                         top_users=top_users,
                         total_users=len(user_stats))

@history_bp.route('/user/<member_id>')
@login_required
def user_detail(member_id):
    """Detail-Ansicht für ein Mitglied mit Pagination"""
    from flask import request, abort
    member = get_member(member_id)
    if not member:
        abort(404)
    
    # Pagination-Parameter
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 100)
    
    # Alle Anmeldungen des Mitglieds (letzte 180 Tage) mit Pagination
    start_date = date.today() - timedelta(days=180)
    pagination = Registration.query.filter(
        Registration.member_id == member_id,
        Registration.datum >= start_date
    ).order_by(Registration.datum.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Gruppiere nach Monat
    from collections import defaultdict
    by_month = defaultdict(int)
    for reg in pagination.items:
        month_key = reg.datum.strftime('%Y-%m')
        by_month[month_key] += 1
    
    return render_template('history_detail.html',
                         member=member,
                         registrations=pagination.items,
                         pagination=pagination,
                         by_month=dict(sorted(by_month.items(), reverse=True)))
