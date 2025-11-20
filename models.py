from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admin'
    
    admin_id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone_number = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    created_event_managers = db.relationship('EventManager', backref='created_by_admin', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        # Handle both new Werkzeug hashes and old placeholder hashes
        if not self.password_hash or self.password_hash.startswith('$2y$10$hash'):
            # This is a placeholder hash, treat as invalid
            return False
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            # Invalid hash format, treat as invalid
            return False
    
    def to_dict(self):
        return {
            'admin_id': self.admin_id,
            'role': self.role,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class EventManager(db.Model):
    __tablename__ = 'event_manager'
    
    event_manager_id = db.Column(db.Integer, primary_key=True)
    created_by_admin_id = db.Column(db.Integer, db.ForeignKey('admin.admin_id'), nullable=False)
    role = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone_number = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    events = db.relationship('Event', backref='event_manager', lazy=True)
    updated_registrations = db.relationship('Registration', backref='updated_by_event_manager', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        # Handle both new Werkzeug hashes and old placeholder hashes
        if not self.password_hash or self.password_hash.startswith('$2y$10$hash'):
            # This is a placeholder hash, treat as invalid
            return False
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            # Invalid hash format, treat as invalid
            return False
    
    def to_dict(self):
        return {
            'event_manager_id': self.event_manager_id,
            'created_by_admin_id': self.created_by_admin_id,
            'role': self.role,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class Participant(db.Model):
    __tablename__ = 'participant'
    
    participant_id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(60), default='attendee')
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    phone_number = db.Column(db.String(30))
    city = db.Column(db.String(80))
    state = db.Column(db.String(60))
    country = db.Column(db.String(60))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    registrations = db.relationship('Registration', backref='participant', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        # Handle both new Werkzeug hashes and old placeholder hashes
        if not self.password_hash or self.password_hash.startswith('$2y$10$hash'):
            # This is a placeholder hash, treat as invalid
            return False
        try:
            return check_password_hash(self.password_hash, password)
        except ValueError:
            # Invalid hash format, treat as invalid
            return False
    
    def to_dict(self):
        return {
            'participant_id': self.participant_id,
            'role': self.role,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class EventType(db.Model):
    __tablename__ = 'event_type'
    
    event_type_id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(100), nullable=False)
    type_description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    events = db.relationship('Event', backref='event_type', lazy=True)

class EventStatus(db.Model):
    __tablename__ = 'event_status'
    
    event_status_id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(60), nullable=False)
    status_description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    events = db.relationship('Event', backref='event_status', lazy=True)

class RegistrationStatus(db.Model):
    __tablename__ = 'registration_status'
    
    registration_status_id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(60), nullable=False)
    status_description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    registrations = db.relationship('Registration', backref='registration_status', lazy=True)

class Event(db.Model):
    __tablename__ = 'event'
    
    event_id = db.Column(db.Integer, primary_key=True)
    event_manager_id = db.Column(db.Integer, db.ForeignKey('event_manager.event_manager_id'), nullable=False)
    event_type_id = db.Column(db.Integer, db.ForeignKey('event_type.event_type_id'), nullable=False)
    event_status_id = db.Column(db.Integer, db.ForeignKey('event_status.event_status_id'), nullable=False)
    event_name = db.Column(db.String(150), nullable=False)
    event_description = db.Column(db.Text)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255))
    total_spots = db.Column(db.Integer)
    registration_deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    registrations = db.relationship('Registration', backref='event', lazy=True)
    
    def to_dict(self):
        return {
            'event_id': self.event_id,
            'event_manager_id': self.event_manager_id,
            'event_type_id': self.event_type_id,
            'event_status_id': self.event_status_id,
            'event_name': self.event_name,
            'event_description': self.event_description,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'location': self.location,
            'total_spots': self.total_spots,
            'registration_deadline': self.registration_deadline.isoformat() if self.registration_deadline else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Registration(db.Model):
    __tablename__ = 'registration'
    
    registration_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.event_id'), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.participant_id'), nullable=False)
    registration_status_id = db.Column(db.Integer, db.ForeignKey('registration_status.registration_status_id'), nullable=False)
    additional_info = db.Column(db.String(255))
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    status_updated_at = db.Column(db.DateTime)
    updated_by_event_manager_id = db.Column(db.Integer, db.ForeignKey('event_manager.event_manager_id'))
    
    def to_dict(self):
        return {
            'registration_id': self.registration_id,
            'event_id': self.event_id,
            'participant_id': self.participant_id,
            'registration_status_id': self.registration_status_id,
            'additional_info': self.additional_info,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'status_updated_at': self.status_updated_at.isoformat() if self.status_updated_at else None,
            'updated_by_event_manager_id': self.updated_by_event_manager_id
        }
