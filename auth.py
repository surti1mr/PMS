from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from models import Admin, EventManager, Participant

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'user_type' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def event_manager_required(f):
    """Decorator to require event manager role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_type' not in session or session['user_type'] not in ['admin', 'event_manager']:
            if request.is_json:
                return jsonify({'error': 'Event manager access required'}), 403
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current logged-in user object"""
    if 'user_id' not in session or 'user_type' not in session:
        return None
    
    user_type = session['user_type']
    user_id = session['user_id']
    
    if user_type == 'admin':
        return Admin.query.get(user_id)
    elif user_type == 'event_manager':
        return EventManager.query.get(user_id)
    elif user_type == 'participant':
        return Participant.query.get(user_id)
    
    return None

def authenticate_user(email, password):
    """Authenticate user across all user types"""
    # Try admin first
    admin = Admin.query.filter_by(email=email, is_active=True).first()
    if admin and admin.check_password(password):
        return admin, 'admin'
    
    # Try event manager
    event_manager = EventManager.query.filter_by(email=email, is_active=True).first()
    if event_manager and event_manager.check_password(password):
        return event_manager, 'event_manager'
    
    # Try participant
    participant = Participant.query.filter_by(email=email, is_active=True).first()
    if participant and participant.check_password(password):
        return participant, 'participant'
    
    return None, None

def login_user(user, user_type):
    """Set session data for logged-in user"""
    session['user_id'] = user.admin_id if user_type == 'admin' else (
        user.event_manager_id if user_type == 'event_manager' else user.participant_id
    )
    session['user_type'] = user_type
    session['user_email'] = user.email
    session['user_name'] = f"{user.first_name} {user.last_name}"
    
    # Set role-specific session data
    if user_type == 'admin':
        session['admin_id'] = user.admin_id
        session['role'] = user.role
    elif user_type == 'event_manager':
        session['event_manager_id'] = user.event_manager_id
        session['role'] = user.role
    elif user_type == 'participant':
        session['participant_id'] = user.participant_id
        session['role'] = user.role

def logout_user():
    """Clear session data"""
    session.clear()
