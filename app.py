from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, Admin, EventManager, Participant, Event, Registration, EventType, EventStatus, RegistrationStatus
from auth import authenticate_user, login_user, logout_user, login_required, get_current_user
from api import api_bp
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Register API blueprint
app.register_blueprint(api_bp)

# Context processor to make current user available in all templates
@app.context_processor
def inject_user():
    return {'current_user': get_current_user()}

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/home')
@login_required
def home():
    user = get_current_user()
    user_type = session.get('user_type')
    from datetime import datetime
    
    if user_type == 'admin':
        # Admin dashboard statistics
        stats = {
            'total_admins': Admin.query.count(),
            'total_event_managers': EventManager.query.count(),
            'total_participants': Participant.query.count(),
            'total_events': Event.query.count(),
            'total_registrations': Registration.query.count(),
            'upcoming_events': Event.query.filter(Event.event_date > datetime.utcnow()).count(),
            'recent_events': Event.query.order_by(Event.created_at.desc()).limit(5).all()
        }
        return render_template('dashboard_admin.html', user=user, stats=stats)
    
    elif user_type == 'event_manager':
        # Event Manager dashboard statistics
        my_events = Event.query.filter_by(event_manager_id=user.event_manager_id).all()
        upcoming_events = [e for e in my_events if e.event_date > datetime.utcnow()]
        
        # Count registrations for all events managed by this event manager
        total_registrations = 0
        if my_events:
            my_event_ids = [e.event_id for e in my_events]
            total_registrations = Registration.query.filter(Registration.event_id.in_(my_event_ids)).count()
        
        stats = {
            'total_events': len(my_events),
            'upcoming_events': len(upcoming_events),
            'total_registrations': total_registrations,
            'recent_events': Event.query.filter_by(event_manager_id=user.event_manager_id).order_by(Event.created_at.desc()).limit(5).all()
        }
        return render_template('dashboard_event_manager.html', user=user, stats=stats)
    
    else:  # participant
        # Participant dashboard statistics
        upcoming_events_all = Event.query.filter(Event.event_date > datetime.utcnow()).count()
        my_registrations = Registration.query.filter_by(participant_id=user.participant_id).all()
        my_registered_events = [reg.event for reg in my_registrations]
        upcoming_registered = [e for e in my_registered_events if e.event_date > datetime.utcnow()]
        
        stats = {
            'available_events': upcoming_events_all,
            'my_registrations': len(my_registrations),
            'upcoming_registered': len(upcoming_registered),
            'recent_events': Event.query.filter(Event.event_date > datetime.utcnow()).order_by(Event.event_date.asc()).limit(5).all()
        }
        return render_template('dashboard_participant.html', user=user, stats=stats)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    message = None
    if request.method == 'POST' and user is not None:
        # Common fields
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.phone_number = request.form.get('phone_number', user.phone_number)

        # Role-specific fields
        user_type = session.get('user_type')
        if user_type == 'participant':
            user.city = request.form.get('city', user.city)
            user.state = request.form.get('state', user.state)
            user.country = request.form.get('country', user.country)

        # Persist changes
        try:
            db.session.commit()
            message = 'Profile updated successfully.'
        except Exception:
            db.session.rollback()
            message = 'Failed to update profile. Please try again.'

    return render_template('profile.html', user=user, message=message)

@app.route('/events')
@login_required
def events():
    user = get_current_user()
    user_type = session.get('user_type')
    
    # Get search query and page number from request
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Events per page
    
    # Build base query
    if user_type == 'event_manager':
        # Event managers only see their own events
        query = Event.query.filter_by(event_manager_id=user.event_manager_id)
    elif user_type == 'admin':
        # Admins see all events
        query = Event.query
    else:
        # Participants see all events (to register)
        query = Event.query
    
    # Apply search filter if provided
    if search_query:
        from sqlalchemy import func
        query = query.filter(func.lower(Event.event_name).like(f'%{search_query.lower()}%'))
    
    # Order by event date and paginate
    query = query.order_by(Event.event_date.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('events.html', events=pagination.items, pagination=pagination, search_query=search_query)

@app.route('/registered_events')
@login_required
def registered_events():
    # Get user's registered events
    user = get_current_user()
    if user and hasattr(user, 'registrations'):
        # For participants, get their registrations with status
        from sqlalchemy.orm import joinedload
        registrations = Registration.query.options(
            joinedload(Registration.event),
            joinedload(Registration.registration_status)
        ).filter_by(participant_id=user.participant_id).order_by(Registration.registered_at.desc()).all()
        
        # Create a list of tuples (event, registration) for easy access in template
        events_with_registrations = [(reg.event, reg) for reg in registrations]
    else:
        events_with_registrations = []
    return render_template('registered_events.html', events_with_registrations=events_with_registrations)

@app.route('/upcoming_events')
@login_required
def upcoming_events():
    user = get_current_user()
    user_type = session.get('user_type')
    from datetime import datetime
    from sqlalchemy import func
    
    # Get current datetime for comparison - only show events with event_date in the future
    current_time = datetime.utcnow()
    
    # Get search query and page number from request
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Events per page
    
    # Build base query with date filter (only future events)
    if user_type == 'event_manager':
        # Event managers only see their own upcoming events (event_date must be > current_time)
        query = Event.query.filter(
            Event.event_manager_id == user.event_manager_id,
            Event.event_date > current_time  # Only future events
        )
    elif user_type == 'admin':
        # Admins see all upcoming events (event_date must be > current_time)
        query = Event.query.filter(
            Event.event_date > current_time  # Only future events
        )
    else:
        # Participants see all upcoming events (event_date must be > current_time)
        query = Event.query.filter(
            Event.event_date > current_time  # Only future events
        )
    
    # Apply search filter if provided
    if search_query:
        query = query.filter(func.lower(Event.event_name).like(f'%{search_query.lower()}%'))
    
    # Order by event date and paginate
    query = query.order_by(Event.event_date.asc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('upcoming_events.html', events=pagination.items, pagination=pagination, search_query=search_query)

@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    user = get_current_user()
    user_type = session.get('user_type')
    
    # Only event managers can add events
    if user_type != 'event_manager':
        abort(403)  # Forbidden
    
    if request.method == 'GET':
        # Get event types and statuses for dropdowns
        event_types = EventType.query.all()
        event_statuses = EventStatus.query.all()
        return render_template('add_event.html', event_types=event_types, event_statuses=event_statuses)
    
    # Handle POST - create new event
    event_name = request.form.get('event_name', '').strip()
    event_description = request.form.get('event_description', '').strip()
    event_date_str = request.form.get('event_date', '').strip()
    event_time_str = request.form.get('event_time', '').strip()
    location = request.form.get('location', '').strip() or None
    total_spots = request.form.get('total_spots', '').strip()
    registration_deadline_date = request.form.get('registration_deadline_date', '').strip()
    registration_deadline_time = request.form.get('registration_deadline_time', '').strip()
    event_type_id = request.form.get('event_type_id', '').strip()
    event_status_id = request.form.get('event_status_id', '').strip()
    
    # Validation
    if not event_name or not event_date_str or not event_type_id or not event_status_id:
        event_types = EventType.query.all()
        event_statuses = EventStatus.query.all()
        return render_template('add_event.html', 
                             event_types=event_types, 
                             event_statuses=event_statuses,
                             error='Please fill in all required fields (Event Name, Date, Type, and Status)')
    
    try:
        from datetime import datetime
        
        # Parse event date and time
        if event_time_str:
            event_datetime_str = f"{event_date_str} {event_time_str}"
            event_date = datetime.strptime(event_datetime_str, '%Y-%m-%d %H:%M')
        else:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
        
        # Parse registration deadline
        registration_deadline = None
        if registration_deadline_date:
            if registration_deadline_time:
                deadline_datetime_str = f"{registration_deadline_date} {registration_deadline_time}"
                registration_deadline = datetime.strptime(deadline_datetime_str, '%Y-%m-%d %H:%M')
            else:
                registration_deadline = datetime.strptime(registration_deadline_date, '%Y-%m-%d')
        
        # Parse total spots
        total_spots_int = None
        if total_spots:
            try:
                total_spots_int = int(total_spots)
            except ValueError:
                pass
        
        # Create new event
        new_event = Event(
            event_manager_id=user.event_manager_id,
            event_type_id=int(event_type_id),
            event_status_id=int(event_status_id),
            event_name=event_name,
            event_description=event_description or None,
            event_date=event_date,
            location=location,
            total_spots=total_spots_int,
            registration_deadline=registration_deadline
        )
        
        db.session.add(new_event)
        db.session.commit()
        
        # Redirect to events page
        return redirect(url_for('events'))
        
    except ValueError as e:
        event_types = EventType.query.all()
        event_statuses = EventStatus.query.all()
        return render_template('add_event.html', 
                             event_types=event_types, 
                             event_statuses=event_statuses,
                             error=f'Invalid date format: {str(e)}')
    except Exception as e:
        db.session.rollback()
        event_types = EventType.query.all()
        event_statuses = EventStatus.query.all()
        return render_template('add_event.html', 
                             event_types=event_types, 
                             event_statuses=event_statuses,
                             error=f'An error occurred: {str(e)}')

@app.route('/events/<int:event_id>')
@login_required
def event_detail(event_id):
    user = get_current_user()
    user_type = session.get('user_type')
    
    # Get the event
    event = Event.query.get_or_404(event_id)
    
    # Check access control for event managers
    if user_type == 'event_manager':
        # Event managers can only view their own events
        if event.event_manager_id != user.event_manager_id:
            abort(403)  # Forbidden - they don't own this event
    
    # Get registrations for this event (for event managers and admins)
    registrations = []
    registration_statuses = []
    approved_count = 0
    if user_type == 'event_manager' or user_type == 'admin':
        from sqlalchemy.orm import joinedload
        from sqlalchemy import or_, func
        registrations = Registration.query.options(
            joinedload(Registration.participant),
            joinedload(Registration.registration_status)
        ).filter_by(event_id=event_id).order_by(Registration.registered_at.desc()).all()
        
        # Get all available registration statuses for dropdown
        registration_statuses = RegistrationStatus.query.all()
        
        # Calculate approved registrations count
        if event.total_spots:
            approved_statuses = RegistrationStatus.query.filter(
                or_(
                    func.lower(RegistrationStatus.status_name).like('%approved%'),
                    func.lower(RegistrationStatus.status_name).like('%accept%'),
                    func.lower(RegistrationStatus.status_name).like('%confirm%')
                )
            ).all()
            approved_status_ids = [s.registration_status_id for s in approved_statuses]
            approved_count = Registration.query.filter(
                Registration.event_id == event_id,
                Registration.registration_status_id.in_(approved_status_ids)
            ).count()
    
    return render_template('event_detail.html', event=event, registrations=registrations, registration_statuses=registration_statuses, user_type=user_type, approved_count=approved_count)

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    user = get_current_user()
    user_type = session.get('user_type')
    
    # Get the event
    event = Event.query.get_or_404(event_id)
    
    # Access control: Event managers can only edit their own events, admins can edit all events
    if user_type == 'event_manager':
        if event.event_manager_id != user.event_manager_id:
            abort(403)  # Forbidden - they don't own this event
    elif user_type != 'admin':
        abort(403)  # Only event managers and admins can edit events
    
    if request.method == 'GET':
        # Get event types and statuses for dropdowns
        event_types = EventType.query.all()
        event_statuses = EventStatus.query.all()
        
        # Format dates for the form inputs
        event_date_str = event.event_date.strftime('%Y-%m-%d') if event.event_date else ''
        event_time_str = event.event_date.strftime('%H:%M') if event.event_date else ''
        registration_deadline_date_str = event.registration_deadline.strftime('%Y-%m-%d') if event.registration_deadline else ''
        registration_deadline_time_str = event.registration_deadline.strftime('%H:%M') if event.registration_deadline else ''
        
        return render_template('edit_event.html', 
                             event=event, 
                             event_types=event_types, 
                             event_statuses=event_statuses,
                             event_date_str=event_date_str,
                             event_time_str=event_time_str,
                             registration_deadline_date_str=registration_deadline_date_str,
                             registration_deadline_time_str=registration_deadline_time_str)
    
    # Handle POST - update event
    event_name = request.form.get('event_name', '').strip()
    event_description = request.form.get('event_description', '').strip()
    event_date_str = request.form.get('event_date', '').strip()
    event_time_str = request.form.get('event_time', '').strip()
    location = request.form.get('location', '').strip() or None
    total_spots = request.form.get('total_spots', '').strip()
    registration_deadline_date = request.form.get('registration_deadline_date', '').strip()
    registration_deadline_time = request.form.get('registration_deadline_time', '').strip()
    event_type_id = request.form.get('event_type_id', '').strip()
    event_status_id = request.form.get('event_status_id', '').strip()
    
    # Validation
    if not event_name or not event_date_str or not event_type_id or not event_status_id:
        event_types = EventType.query.all()
        event_statuses = EventStatus.query.all()
        event_date_str = event.event_date.strftime('%Y-%m-%d') if event.event_date else ''
        event_time_str = event.event_date.strftime('%H:%M') if event.event_date else ''
        registration_deadline_date_str = event.registration_deadline.strftime('%Y-%m-%d') if event.registration_deadline else ''
        registration_deadline_time_str = event.registration_deadline.strftime('%H:%M') if event.registration_deadline else ''
        return render_template('edit_event.html', 
                             event=event,
                             event_types=event_types, 
                             event_statuses=event_statuses,
                             event_date_str=event_date_str,
                             event_time_str=event_time_str,
                             registration_deadline_date_str=registration_deadline_date_str,
                             registration_deadline_time_str=registration_deadline_time_str,
                             error='Please fill in all required fields (Event Name, Date, Type, and Status)')
    
    try:
        from datetime import datetime
        
        # Parse event date and time
        if event_time_str:
            event_datetime_str = f"{event_date_str} {event_time_str}"
            event_date = datetime.strptime(event_datetime_str, '%Y-%m-%d %H:%M')
        else:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
        
        # Parse registration deadline
        registration_deadline = None
        if registration_deadline_date:
            if registration_deadline_time:
                deadline_datetime_str = f"{registration_deadline_date} {registration_deadline_time}"
                registration_deadline = datetime.strptime(deadline_datetime_str, '%Y-%m-%d %H:%M')
            else:
                registration_deadline = datetime.strptime(registration_deadline_date, '%Y-%m-%d')
        
        # Parse total spots
        total_spots_int = None
        if total_spots:
            try:
                total_spots_int = int(total_spots)
            except ValueError:
                pass
        
        # Update event
        event.event_name = event_name
        event.event_description = event_description or None
        event.event_date = event_date
        event.location = location
        event.total_spots = total_spots_int
        event.registration_deadline = registration_deadline
        event.event_type_id = int(event_type_id)
        event.event_status_id = int(event_status_id)
        # Note: event_manager_id should not be changed, so we keep it as is
        
        db.session.commit()
        
        # Redirect to event detail page
        return redirect(url_for('event_detail', event_id=event_id))
        
    except ValueError as e:
        event_types = EventType.query.all()
        event_statuses = EventStatus.query.all()
        event_date_str = event.event_date.strftime('%Y-%m-%d') if event.event_date else ''
        event_time_str = event.event_date.strftime('%H:%M') if event.event_date else ''
        registration_deadline_date_str = event.registration_deadline.strftime('%Y-%m-%d') if event.registration_deadline else ''
        registration_deadline_time_str = event.registration_deadline.strftime('%H:%M') if event.registration_deadline else ''
        return render_template('edit_event.html', 
                             event=event,
                             event_types=event_types, 
                             event_statuses=event_statuses,
                             event_date_str=event_date_str,
                             event_time_str=event_time_str,
                             registration_deadline_date_str=registration_deadline_date_str,
                             registration_deadline_time_str=registration_deadline_time_str,
                             error=f'Invalid date format: {str(e)}')
    except Exception as e:
        db.session.rollback()
        event_types = EventType.query.all()
        event_statuses = EventStatus.query.all()
        event_date_str = event.event_date.strftime('%Y-%m-%d') if event.event_date else ''
        event_time_str = event.event_date.strftime('%H:%M') if event.event_date else ''
        registration_deadline_date_str = event.registration_deadline.strftime('%Y-%m-%d') if event.registration_deadline else ''
        registration_deadline_time_str = event.registration_deadline.strftime('%H:%M') if event.registration_deadline else ''
        return render_template('edit_event.html', 
                             event=event,
                             event_types=event_types, 
                             event_statuses=event_statuses,
                             event_date_str=event_date_str,
                             event_time_str=event_time_str,
                             registration_deadline_date_str=registration_deadline_date_str,
                             registration_deadline_time_str=registration_deadline_time_str,
                             error=f'An error occurred: {str(e)}')

@app.route('/register/<int:event_id>', methods=['GET', 'POST'])
@login_required
def register_event(event_id):
    user = get_current_user()
    user_type = session.get('user_type')
    
    # Only participants can register for events
    if user_type != 'participant':
        abort(403)  # Forbidden
    
    # Get the event
    event = Event.query.get_or_404(event_id)
    
    # Check if already registered
    existing_registration = Registration.query.filter_by(
        event_id=event_id,
        participant_id=user.participant_id
    ).first()
    
    if existing_registration:
        return render_template('register_event.html', 
                             event=event, 
                             error='You have already registered for this event.')
    
    # Check if registration deadline has passed
    from datetime import datetime
    if event.registration_deadline and datetime.utcnow() > event.registration_deadline:
        return render_template('register_event.html', 
                             event=event, 
                             error='Registration deadline has passed for this event.')
    
    # Check if event has available spots (exclude cancelled and rejected registrations)
    if event.total_spots:
        from sqlalchemy import or_, func
        from models import RegistrationStatus
        
        # Get status IDs that should NOT count towards available spots (cancelled, rejected)
        excluded_statuses = RegistrationStatus.query.filter(
            or_(
                func.lower(RegistrationStatus.status_name).like('%cancel%'),
                func.lower(RegistrationStatus.status_name).like('%reject%'),
                func.lower(RegistrationStatus.status_name).like('%declined%')
            )
        ).all()
        excluded_status_ids = [s.registration_status_id for s in excluded_statuses]
        
        # Count only active registrations (not cancelled/rejected)
        if excluded_status_ids:
            current_registrations = Registration.query.filter(
                Registration.event_id == event_id,
                ~Registration.registration_status_id.in_(excluded_status_ids)
            ).count()
        else:
            # If no excluded statuses found, count all (fallback)
            current_registrations = Registration.query.filter_by(event_id=event_id).count()
        
        if current_registrations >= event.total_spots:
            return render_template('register_event.html', 
                                 event=event, 
                                 error='This event is full. No more spots available.')
    
    if request.method == 'GET':
        return render_template('register_event.html', event=event)
    
    # Handle POST - process registration
    additional_info = request.form.get('additional_info', '').strip()
    
    try:
        from sqlalchemy import func
        # Get default pending status - try multiple variations
        pending_status = RegistrationStatus.query.filter(
            func.lower(RegistrationStatus.status_name) == 'pending'
        ).first()
        
        # If still not found, try status_id = 1 (common default)
        if not pending_status:
            pending_status = RegistrationStatus.query.filter_by(registration_status_id=1).first()
        
        # If still not found, get the first available status
        if not pending_status:
            pending_status = RegistrationStatus.query.first()
        
        # Final check - if no statuses exist at all
        if not pending_status:
            return render_template('register_event.html', 
                                 event=event, 
                                 error='Registration system error: No registration statuses found.')
        
        # Create new registration
        registration = Registration(
            event_id=event_id,
            participant_id=user.participant_id,
            registration_status_id=pending_status.registration_status_id,
            additional_info=additional_info or None
        )
        
        db.session.add(registration)
        db.session.commit()
        
        # Redirect to registered events page or event detail page
        return redirect(url_for('registered_events'))
        
    except Exception as e:
        db.session.rollback()
        return render_template('register_event.html', 
                             event=event, 
                             error=f'An error occurred during registration: {str(e)}')

@app.route('/add_event_manager', methods=['GET', 'POST'])
@login_required
def add_event_manager():
    user = get_current_user()
    user_type = session.get('user_type')
    
    # Only admins can add event managers
    if user_type != 'admin':
        abort(403)  # Forbidden
    
    if request.method == 'GET':
        return render_template('add_event_manager.html')
    
    # Handle POST - create new event manager
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    phone_number = request.form.get('phone_number', '').strip() or None
    role = request.form.get('role', 'Event Manager').strip()
    
    # Validation
    if not email or not password or not first_name or not last_name:
        return render_template('add_event_manager.html', 
                             error='Please fill in all required fields (Email, Password, First Name, and Last Name)')
    
    if password != confirm_password:
        return render_template('add_event_manager.html', error='Passwords do not match. Please try again.')
    
    if len(password) < 6:
        return render_template('add_event_manager.html', error='Password must be at least 6 characters long.')
    
    # Check if email already exists
    existing_manager = EventManager.query.filter_by(email=email).first()
    existing_admin = Admin.query.filter_by(email=email).first()
    existing_participant = Participant.query.filter_by(email=email).first()
    
    if existing_manager or existing_admin or existing_participant:
        return render_template('add_event_manager.html', 
                             error='Email already exists. Please use a different email address.')
    
    try:
        # Create new event manager
        new_event_manager = EventManager(
            created_by_admin_id=user.admin_id,
            role=role,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            is_active=True
        )
        new_event_manager.set_password(password)
        
        db.session.add(new_event_manager)
        db.session.commit()
        
        # Redirect to dashboard with success
        return redirect(url_for('home'))
        
    except Exception as e:
        db.session.rollback()
        return render_template('add_event_manager.html', 
                             error=f'An error occurred while creating the event manager: {str(e)}')

@app.route('/all_event_managers')
@login_required
def all_event_managers():
    user = get_current_user()
    user_type = session.get('user_type')
    
    # Only admins can view all event managers
    if user_type != 'admin':
        abort(403)  # Forbidden
    
    # Get search query and page number from request
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Items per page
    
    # Build base query
    query = EventManager.query
    
    # Apply search filter if provided (search by email)
    if search_query:
        from sqlalchemy import func
        query = query.filter(func.lower(EventManager.email).like(f'%{search_query.lower()}%'))
    
    # Order by created_at and paginate
    query = query.order_by(EventManager.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('all_event_managers.html', 
                         event_managers=pagination.items,
                         pagination=pagination,
                         search_query=search_query)

@app.route('/edit_event_manager/<int:manager_id>', methods=['GET', 'POST'])
@login_required
def edit_event_manager(manager_id):
    user = get_current_user()
    user_type = session.get('user_type')
    
    # Only admins can edit event managers
    if user_type != 'admin':
        abort(403)  # Forbidden
    
    # Get the event manager
    event_manager = EventManager.query.get_or_404(manager_id)
    
    if request.method == 'GET':
        return render_template('edit_event_manager.html', manager=event_manager)
    
    # Handle POST - update event manager
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    phone_number = request.form.get('phone_number', '').strip() or None
    role = request.form.get('role', 'Event Manager').strip()
    is_active = request.form.get('is_active') == 'on'
    
    # Validation
    if not email or not first_name or not last_name:
        return render_template('edit_event_manager.html', 
                             manager=event_manager,
                             error='Please fill in all required fields (Email, First Name, and Last Name)')
    
    # If password is provided, validate it
    if password:
        if password != confirm_password:
            return render_template('edit_event_manager.html', 
                                 manager=event_manager,
                                 error='Passwords do not match. Please try again.')
        
        if len(password) < 6:
            return render_template('edit_event_manager.html', 
                                 manager=event_manager,
                                 error='Password must be at least 6 characters long.')
    
    # Check if email already exists (but not for current manager)
    if email != event_manager.email:
        existing_manager = EventManager.query.filter_by(email=email).first()
        existing_admin = Admin.query.filter_by(email=email).first()
        existing_participant = Participant.query.filter_by(email=email).first()
        
        if existing_manager or existing_admin or existing_participant:
            return render_template('edit_event_manager.html', 
                                 manager=event_manager,
                                 error='Email already exists. Please use a different email address.')
    
    try:
        # Update event manager
        event_manager.email = email
        event_manager.first_name = first_name
        event_manager.last_name = last_name
        event_manager.phone_number = phone_number
        event_manager.role = role
        event_manager.is_active = is_active
        
        # Update password only if provided
        if password:
            event_manager.set_password(password)
        
        db.session.commit()
        
        # Redirect to all event managers page
        return redirect(url_for('all_event_managers'))
        
    except Exception as e:
        db.session.rollback()
        return render_template('edit_event_manager.html', 
                             manager=event_manager,
                             error=f'An error occurred while updating the event manager: {str(e)}')

@app.route('/all_participants')
@login_required
def all_participants():
    user = get_current_user()
    user_type = session.get('user_type')
    
    # Only admins can view all participants
    if user_type != 'admin':
        abort(403)  # Forbidden
    
    # Get search query and page number from request
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Items per page
    
    # Build base query
    query = Participant.query
    
    # Apply search filter if provided (search by email)
    if search_query:
        from sqlalchemy import func
        query = query.filter(func.lower(Participant.email).like(f'%{search_query.lower()}%'))
    
    # Order by created_at and paginate
    query = query.order_by(Participant.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('all_participants.html', 
                         participants=pagination.items,
                         pagination=pagination,
                         search_query=search_query)

@app.route('/edit_participant/<int:participant_id>', methods=['GET', 'POST'])
@login_required
def edit_participant(participant_id):
    user = get_current_user()
    user_type = session.get('user_type')
    
    # Only admins can edit participants
    if user_type != 'admin':
        abort(403)  # Forbidden
    
    # Get the participant
    participant = Participant.query.get_or_404(participant_id)
    
    if request.method == 'GET':
        return render_template('edit_participant.html', participant=participant)
    
    # Handle POST - update participant
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    phone_number = request.form.get('phone_number', '').strip() or None
    city = request.form.get('city', '').strip() or None
    state = request.form.get('state', '').strip() or None
    country = request.form.get('country', '').strip() or None
    role = request.form.get('role', 'attendee').strip()
    is_active = request.form.get('is_active') == 'on'
    
    # Validation
    if not email or not first_name or not last_name:
        return render_template('edit_participant.html', 
                             participant=participant,
                             error='Please fill in all required fields (Email, First Name, and Last Name)')
    
    # If password is provided, validate it
    if password:
        if password != confirm_password:
            return render_template('edit_participant.html', 
                                 participant=participant,
                                 error='Passwords do not match. Please try again.')
        
        if len(password) < 6:
            return render_template('edit_participant.html', 
                                 participant=participant,
                                 error='Password must be at least 6 characters long.')
    
    # Check if email already exists (but not for current participant)
    if email != participant.email:
        existing_manager = EventManager.query.filter_by(email=email).first()
        existing_admin = Admin.query.filter_by(email=email).first()
        existing_participant = Participant.query.filter_by(email=email).first()
        
        if existing_manager or existing_admin or existing_participant:
            return render_template('edit_participant.html', 
                                 participant=participant,
                                 error='Email already exists. Please use a different email address.')
    
    try:
        # Update participant
        participant.email = email
        participant.first_name = first_name
        participant.last_name = last_name
        participant.phone_number = phone_number
        participant.city = city
        participant.state = state
        participant.country = country
        participant.role = role
        participant.is_active = is_active
        
        # Update password only if provided
        if password:
            participant.set_password(password)
        
        db.session.commit()
        
        # Redirect to all participants page
        return redirect(url_for('all_participants'))
        
    except Exception as e:
        db.session.rollback()
        return render_template('edit_participant.html', 
                             participant=participant,
                             error=f'An error occurred while updating the participant: {str(e)}')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    # Handle POST - process signup form
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    phone_number = request.form.get('phone_number', '').strip() or None
    city = request.form.get('city', '').strip() or None
    state = request.form.get('state', '').strip() or None
    country = request.form.get('country', '').strip() or None
    
    # Validation
    if not email or not password or not first_name or not last_name:
        return render_template('signup.html', error='Please fill in all required fields')
    
    if password != confirm_password:
        return render_template('signup.html', error='Passwords do not match')
    
    if len(password) < 6:
        return render_template('signup.html', error='Password must be at least 6 characters long')
    
    # Check if email already exists in any user table
    existing_participant = Participant.query.filter_by(email=email).first()
    existing_admin = Admin.query.filter_by(email=email).first()
    existing_manager = EventManager.query.filter_by(email=email).first()
    
    if existing_participant or existing_admin or existing_manager:
        return render_template('signup.html', error='Email already registered. Please use a different email or sign in.')
    
    # Create new participant account (only Participant role can be created from signup)
    try:
        new_participant = Participant(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            city=city,
            state=state,
            country=country,
            role='Participant',  # Default role for participants
            is_active=True
        )
        new_participant.set_password(password)
        
        db.session.add(new_participant)
        db.session.commit()
        
        # Auto-login the new participant
        login_user(new_participant, 'participant')
        
        # Redirect to home page
        return redirect(url_for('home'))
        
    except Exception as e:
        db.session.rollback()
        return render_template('signup.html', error=f'An error occurred during registration: {str(e)}')

@app.route('/submit_login', methods=['POST'])
def submit_login():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    
    # Validation
    if not email or not password:
        return render_template('login.html', error='Please enter both email and password.')
    
    # Normalize email
    email = email.lower()
    
    # Authenticate user
    user, user_type = authenticate_user(email, password)
    
    if user and user_type:
        login_user(user, user_type)
        return redirect(url_for('home'))
    else:
        # Check if email exists but password is wrong
        from models import Admin, EventManager, Participant
        admin_exists = Admin.query.filter_by(email=email).first()
        manager_exists = EventManager.query.filter_by(email=email).first()
        participant_exists = Participant.query.filter_by(email=email).first()
        
        if admin_exists or manager_exists or participant_exists:
            return render_template('login.html', error='Invalid password. Please check your password and try again.')
        else:
            return render_template('login.html', error='Invalid email or password. Please check your credentials and try again.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
