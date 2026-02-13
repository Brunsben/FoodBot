"""System-Verwaltung: Updates, Backups, Logs"""
import subprocess
import os
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template
from .auth import login_required
from .models import db, AdminLog

logger = logging.getLogger(__name__)
system_bp = Blueprint('system', __name__, url_prefix='/system')

@system_bp.route('/update', methods=['POST'])
@login_required
def git_update():
    """Git pull und Service-Restart"""
    try:
        # Git status prüfen
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        if result.stdout.strip():
            return jsonify({
                'success': False,
                'message': 'Lokale Änderungen vorhanden. Bitte manuell committen.'
            })
        
        # Git pull
        pull_result = subprocess.run(
            ['git', 'pull'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        # Log schreiben
        AdminLog(
            admin_user=request.remote_addr,
            action='system_update',
            details=f"Git pull: {pull_result.stdout}"
        ).save()
        
        if pull_result.returncode == 0:
            # Service restart
            restart_result = subprocess.run(
                ['sudo', 'systemctl', 'restart', 'foodbot'],
                capture_output=True,
                text=True
            )
            
            return jsonify({
                'success': True,
                'message': 'Update erfolgreich. Service wird neu gestartet...',
                'output': pull_result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Git pull fehlgeschlagen',
                'error': pull_result.stderr
            })
            
    except Exception as e:
        logger.error(f"Update-Fehler: {e}")
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        })

@system_bp.route('/backup', methods=['POST'])
@login_required
def create_backup():
    """Datenbank-Backup erstellen"""
    try:
        from flask import current_app
        # DB-Pfad aus SQLAlchemy Config extrahieren
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            db_path = os.path.join(current_app.instance_path, os.path.basename(db_path))
        
        backup_dir = 'backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'foodbot_{timestamp}.db')
        
        import shutil
        shutil.copy2(db_path, backup_path)
        
        # Log
        AdminLog(
            admin_user=request.remote_addr,
            action='backup_created',
            details=f"Backup: {backup_path}"
        ).save()
        
        return jsonify({
            'success': True,
            'message': f'Backup erstellt: {backup_path}'
        })
        
    except Exception as e:
        logger.error(f"Backup-Fehler: {e}")
        return jsonify({
            'success': False,
            'message': f'Fehler: {str(e)}'
        })

@system_bp.route('/logs', methods=['GET'])
@login_required
def get_admin_logs():
    """Admin-Log anzeigen"""
    logs = AdminLog.query.order_by(AdminLog.timestamp.desc()).limit(100).all()
    return jsonify({
        'logs': [{
            'timestamp': log.timestamp.isoformat(),
            'admin': log.admin_user,
            'action': log.action,
            'details': log.details
        } for log in logs]
    })

@system_bp.route('/info', methods=['GET'])
@login_required
def system_info():
    """System-Informationen"""
    try:
        # Git-Version
        git_result = subprocess.run(
            ['git', 'log', '-1', '--oneline'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        
        # Disk Space
        disk_result = subprocess.run(
            ['df', '-h', '/'],
            capture_output=True,
            text=True
        )
        
        return jsonify({
            'git_version': git_result.stdout.strip(),
            'disk_space': disk_result.stdout,
            'python_version': subprocess.run(['python3', '--version'], capture_output=True, text=True).stdout.strip()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})
