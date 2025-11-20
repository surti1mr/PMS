from flask import Blueprint, request, jsonify, session
from models import db, Admin, EventManager, Participant, Event, Registration
from auth import authenticate_user, login_user, logout_user, login_required, get_current_user
from datetime import datetime
from sqlalchemy import or_, func

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/login', methods=['POST'])
def api_login():
    """API endpoint for user login"""
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        user, user_type = authenticate_user(email, password)
        
        if user and user_type:
            login_user(user, user_type)
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.admin_id if user_type == 'admin' else (
                        user.event_manager_id if user_type == 'event_manager' else user.participant_id
                    ),
                    'type': user_type,
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}",
                    'role': user.role
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@api_bp.route('/logout', methods=['POST'])
def api_logout():
    """API endpoint for user logout"""
    try:
        logout_user()
        return jsonify({'success': True, 'message': 'Logout successful'}), 200
    except Exception as e:
        return jsonify({'error': 'Logout failed', 'details': str(e)}), 500

@api_bp.route('/profile', methods=['GET'])
@login_required
def api_profile():
    """API endpoint to get current user profile"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get profile', 'details': str(e)}), 500

@api_bp.route('/events', methods=['GET'])
@login_required
def api_events():
    """API endpoint to get events"""
    try:
        from auth import get_current_user
        user = get_current_user()
        user_type = session.get('user_type')
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', None)
        
        query = Event.query
        
        # Filter events based on user role
        if user_type == 'event_manager':
            # Event managers only see their own events
            query = query.filter(Event.event_manager_id == user.event_manager_id)
        # Admins and participants see all events
        
        if status:
            query = query.filter(Event.event_status_id == status)
        
        events = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'events': [event.to_dict() for event in events.items],
            'pagination': {
                'page': events.page,
                'pages': events.pages,
                'per_page': events.per_page,
                'total': events.total
            }
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get events', 'details': str(e)}), 500

@api_bp.route('/events/<int:event_id>', methods=['GET'])
@login_required
def api_get_event(event_id):
    """API endpoint to get specific event"""
    try:
        from auth import get_current_user
        user = get_current_user()
        user_type = session.get('user_type')
        
        event = Event.query.get_or_404(event_id)
        
        # Check access control for event managers
        if user_type == 'event_manager':
            # Event managers can only view their own events
            if event.event_manager_id != user.event_manager_id:
                return jsonify({'error': 'Access denied. You can only view your own events.'}), 403
        
        return jsonify({
            'success': True,
            'event': event.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get event', 'details': str(e)}), 500

@api_bp.route('/register/<int:event_id>', methods=['POST'])
@login_required
def api_register_event(event_id):
    """API endpoint for participants to register for events"""
    try:
        if session['user_type'] != 'participant':
            return jsonify({'error': 'Only participants can register for events'}), 403
        
        event = Event.query.get_or_404(event_id)
        participant_id = session['participant_id']
        
        # Check if already registered
        existing_registration = Registration.query.filter_by(
            event_id=event_id, 
            participant_id=participant_id
        ).first()
        
        if existing_registration:
            return jsonify({'error': 'Already registered for this event'}), 400
        
        # Check if registration deadline has passed
        if event.registration_deadline and datetime.utcnow() > event.registration_deadline:
            return jsonify({'error': 'Registration deadline has passed'}), 400
        
        # Check if event has available spots (exclude cancelled and rejected registrations)
        if event.total_spots:
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
                return jsonify({'error': 'This event is full. No more spots available.'}), 400
        
        # Create new registration
        registration = Registration(
            event_id=event_id,
            participant_id=participant_id,
            registration_status_id=1,  # Pending status
            additional_info=request.json.get('additional_info', '')
        )
        
        db.session.add(registration)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'registration': registration.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@api_bp.route('/my-registrations', methods=['GET'])
@login_required
def api_my_registrations():
    """API endpoint for participants to get their registrations"""
    try:
        if session['user_type'] != 'participant':
            return jsonify({'error': 'Only participants can view their registrations'}), 403
        
        participant_id = session['participant_id']
        registrations = Registration.query.filter_by(participant_id=participant_id).all()
        
        return jsonify({
            'success': True,
            'registrations': [reg.to_dict() for reg in registrations]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to get registrations', 'details': str(e)}), 500

@api_bp.route('/event_manager/<int:manager_id>', methods=['DELETE'])
@login_required
def api_delete_event_manager(manager_id):
    """API endpoint for admins to delete event managers"""
    try:
        user = get_current_user()
        user_type = session.get('user_type')
        
        # Only admins can delete event managers
        if user_type != 'admin':
            return jsonify({'error': 'Access denied. Only admins can delete event managers.'}), 403
        
        event_manager = EventManager.query.get_or_404(manager_id)
        
        # Check if event manager has any events
        events_count = Event.query.filter_by(event_manager_id=manager_id).count()
        if events_count > 0:
            return jsonify({
                'error': f'Cannot delete event manager. They have {events_count} event(s) associated with them. Please reassign or delete those events first.'
            }), 400
        
        db.session.delete(event_manager)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event manager deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete event manager', 'details': str(e)}), 500

@api_bp.route('/registration/<int:registration_id>/status', methods=['PUT'])
@login_required
def api_update_registration_status(registration_id):
    """API endpoint for event managers to update registration status"""
    try:
        user = get_current_user()
        user_type = session.get('user_type')
        
        # Only event managers can update registration status
        if user_type != 'event_manager':
            return jsonify({'error': 'Access denied. Only event managers can update registration status.'}), 403
        
        data = request.get_json()
        if not data or 'registration_status_id' not in data:
            return jsonify({'error': 'Registration status ID is required'}), 400
        
        new_status_id = int(data['registration_status_id'])
        
        # Get the registration
        registration = Registration.query.get_or_404(registration_id)
        
        # Verify the event belongs to this event manager
        event = Event.query.get_or_404(registration.event_id)
        if event.event_manager_id != user.event_manager_id:
            return jsonify({'error': 'Access denied. You can only update registrations for your own events.'}), 403
        
        # Verify the status exists
        from models import RegistrationStatus
        status = RegistrationStatus.query.get(new_status_id)
        if not status:
            return jsonify({'error': 'Invalid registration status'}), 400
        
        # Check if trying to approve and if event has available spots
        status_name_lower = status.status_name.lower()
        is_approving = 'approved' in status_name_lower or 'accept' in status_name_lower or 'confirmed' in status_name_lower
        
        if is_approving and event.total_spots:
            # Get current approved registrations count
            approved_statuses = RegistrationStatus.query.filter(
                or_(
                    func.lower(RegistrationStatus.status_name).like('%approved%'),
                    func.lower(RegistrationStatus.status_name).like('%accept%'),
                    func.lower(RegistrationStatus.status_name).like('%confirm%')
                )
            ).all()
            approved_status_ids = [s.registration_status_id for s in approved_statuses]
            
            # Count currently approved registrations for this event
            current_approved_count = Registration.query.filter(
                Registration.event_id == event.event_id,
                Registration.registration_status_id.in_(approved_status_ids)
            ).count()
            
            # Check if current registration is already approved (if changing from approved to approved, no change)
            current_registration_status = RegistrationStatus.query.get(registration.registration_status_id)
            is_currently_approved = False
            if current_registration_status:
                current_status_name_lower = current_registration_status.status_name.lower()
                is_currently_approved = ('approved' in current_status_name_lower or 
                                        'accept' in current_status_name_lower or 
                                        'confirm' in current_status_name_lower)
            
            # If not currently approved, we're adding a new approval
            if not is_currently_approved:
                if current_approved_count >= event.total_spots:
                    return jsonify({
                        'error': f'Cannot approve registration. Event is full ({event.total_spots} spots available, {current_approved_count} already approved).'
                    }), 400
        
        # Update registration status
        from datetime import datetime
        registration.registration_status_id = new_status_id
        registration.status_updated_at = datetime.utcnow()
        registration.updated_by_event_manager_id = user.event_manager_id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration status updated successfully',
            'registration': registration.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update registration status', 'details': str(e)}), 500

@api_bp.route('/cancel-registration/<int:event_id>', methods=['POST'])
@login_required
def api_cancel_registration(event_id):
    """API endpoint for participants to cancel their registration"""
    try:
        user = get_current_user()
        user_type = session.get('user_type')
        
        # Only participants can cancel their own registrations
        if user_type != 'participant':
            return jsonify({'error': 'Access denied. Only participants can cancel registrations.'}), 403
        
        # Get the event
        event = Event.query.get_or_404(event_id)
        
        # Get the participant's registration for this event
        registration = Registration.query.filter_by(
            event_id=event_id,
            participant_id=user.participant_id
        ).first()
        
        if not registration:
            return jsonify({'error': 'Registration not found for this event.'}), 404
        
        # Check if already cancelled
        from models import RegistrationStatus
        if registration.registration_status:
            status_name_lower = registration.registration_status.status_name.lower()
            if 'cancel' in status_name_lower:
                return jsonify({'error': 'Registration is already cancelled.'}), 400
        
        # Find or get cancelled status
        cancelled_status = RegistrationStatus.query.filter(
            func.lower(RegistrationStatus.status_name).like('%cancel%')
        ).first()
        
        # If cancelled status doesn't exist, try to find a rejected status as fallback
        if not cancelled_status:
            cancelled_status = RegistrationStatus.query.filter(
                func.lower(RegistrationStatus.status_name).like('%reject%')
            ).first()
        
        # If still not found, get the first available status (shouldn't happen in production)
        if not cancelled_status:
            cancelled_status = RegistrationStatus.query.first()
            if not cancelled_status:
                return jsonify({'error': 'Registration system error: No registration statuses found.'}), 500
        
        # Update registration status to cancelled
        from datetime import datetime
        registration.registration_status_id = cancelled_status.registration_status_id
        registration.status_updated_at = datetime.utcnow()
        registration.updated_by_event_manager_id = None  # Participant cancelled, not event manager
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration cancelled successfully',
            'registration': registration.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel registration', 'details': str(e)}), 500

@api_bp.route('/participant/<int:participant_id>', methods=['DELETE'])
@login_required
def api_delete_participant(participant_id):
    """API endpoint for admins to delete participants"""
    try:
        user = get_current_user()
        user_type = session.get('user_type')
        
        # Only admins can delete participants
        if user_type != 'admin':
            return jsonify({'error': 'Access denied. Only admins can delete participants.'}), 403
        
        participant = Participant.query.get_or_404(participant_id)
        
        # Check if participant has any registrations
        registrations_count = Registration.query.filter_by(participant_id=participant_id).count()
        if registrations_count > 0:
            return jsonify({
                'error': f'Cannot delete participant. They have {registrations_count} registration(s) associated with them. Please remove those registrations first.'
            }), 400
        
        db.session.delete(participant)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Participant deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete participant', 'details': str(e)}), 500

@api_bp.route('/health', methods=['GET'])
def api_health():
    """API health check endpoint"""
    try:
        # Test database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'success': True,
            'message': 'API is healthy',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'API health check failed',
            'database': 'disconnected',
            'error': str(e)
        }), 500
